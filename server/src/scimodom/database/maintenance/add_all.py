#! /usr/bin/env python3

"""Wrapper script to add projects and dataset
from project templates (json only).

NOTE: For maintainers to batch add data, but these extra (optional)
fields are required in the template: file, data_title.
This script is not particularly efficient nor safe, but it is not
intended for general usage: we just want to batch add some data
to the DB in the short-term.
"""

from argparse import ArgumentParser, SUPPRESS
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import json
import logging
import os
from pathlib import Path
from subprocess import Popen, PIPE

from scimodom.config import Config
from scimodom.database.database import make_session
from scimodom.services.project import ProjectService
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)

extra_cols = ["file", "data_title"]


def _get_templates(args):
    all_paths = []
    for f in args.project_template:
        path = Path(args.directory, f"{f}.json")
        if not path.is_file():
            msg = f"Template {path} missing. Skipping!"
            logger.error(msg)
            continue
        all_paths.append(path)
    return all_paths


def _get_projects(templates):
    all_projects = []
    for template in templates:
        handle = open(template, "r")
        project = json.load(handle)
        project["path"] = template.as_posix()
        for d in utils.to_list(project["metadata"]):
            try:
                utils.check_keys_exist(d.keys(), extra_cols)
            except:
                msg = f"Missing keys in {template} for metadata. Skipping project alltogether!"
                logger.error(msg)
                break
        else:
            all_projects.append(project)
        handle.close()
    return all_projects


def _get_dataset(project):
    d = defaultdict(list)
    for metadata in project["metadata"]:
        d[metadata["file"]].append(metadata)
    return d


def _add_dataset(key, data, smid, args):
    metadata = data[key]
    d = metadata[0]
    if len(metadata) > 1:
        # assume all remaining entries are identical...
        # this might not be true...
        d["rna"] = " ".join([m["rna"] for m in metadata])
        d["modomics_id"] = " ".join([m["modomics_id"] for m in metadata])
    call = [
        "add-dataset",
        "-smid",
        smid,
        "--title",
        f'"{d["data_title"]}"',
        "--file",
        Path(args.directory, key).as_posix(),
        "-o",
        str(d["organism"]["taxa_id"]),
        "-a",
        d["organism"]["assembly"],
        "-m",
        d["modomics_id"],
        "-rna",
        d["rna"],
        "--modomics",
        "-t",
        f'"{d["tech"]}"',
        "-cto",
        f'"{d["organism"]["cto"]}"',
        "-db",
        args.database,
    ]
    p = Popen(f"printf 'Y' | {' '.join(call)}", stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = p.communicate()

    return key, (p.returncode, stdout, stderr)


def main():
    parser = ArgumentParser(
        add_help=False, description="""Add project and dataset from template."""
    )

    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")

    required.add_argument(
        "-d",
        "--directory",
        help="Directory where project templates and files are located.",
        type=str,
        required=True,
    )

    required.add_argument(
        "-pt",
        "--project-template",
        help="Space-separated list of project templates (file name only w/o extension)",
        nargs="+",
        type=str,
        required=True,
    )

    optional.add_argument(
        "-h",
        "--help",
        action="help",
        default=SUPPRESS,
        help="show this help message and exit",
    )

    optional.add_argument(
        "-db",
        "--database",
        help="Database URI",
        type=str,
        default=Config.DATABASE_URI,
    )

    optional.add_argument(
        "--map-async",
        help="""Concurrent calls to 'add-dataset'. Caution:
        filling of the /tmp space due to concurrent pybedtools
        operations may occur!""",
        action="store_true",
    )

    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)

    engine, session_factory = make_session(args.database)
    session = session_factory()

    templates = _get_templates(args)
    projects = _get_projects(templates)

    # add projects
    for project in projects:
        try:
            service = ProjectService(session, project)
            service.create_project()
            project["SMID"] = service.get_smid()
        except Exception as e:
            msg = (
                f"Failed to add project template {project['path']}. "
                f"Exception is {e}. Skipping!"
            )
            logger.error(msg)

    # add data
    for project in projects:
        smid = project.get("SMID", None)
        if smid is None:
            msg = f"Missing SMID! Failed to add project data for {project['title']}. Skipping!"
            logger.error(msg)
            continue
        metadata = _get_dataset(project)
        if not args.map_async:
            for key in metadata.keys():
                _, ret = _add_dataset(key, metadata, smid, args)
                msg = (
                    f"Subprocess returned with {ret[0]} for dataset {key}. "
                    f"Traceback stdout: {ret[1]}. "
                    f"Traceback stderr: {ret[2]}."
                )
                if not ret[0] == 0:
                    logger.error(msg)
                else:
                    logger.warning(msg)
        else:
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as ppe:
                for key, ret in ppe.map(
                    partial(_add_dataset, data=metadata, smid=smid, args=args),
                    metadata.keys(),
                ):
                    msg = (
                        f"Subprocess returned with {ret[0]} for dataset {key}. "
                        f"Traceback stdout: {ret[1]}. "
                        f"Traceback stderr: {ret[2]}."
                    )
                    if not ret[0] == 0:
                        logger.error(msg)
                    else:
                        logger.warning(msg)


if __name__ == "__main__":
    main()
