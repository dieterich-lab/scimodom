#! /usr/bin/env python3

"""Wrapper script to add projects and dataset
from project templates (json only).

NOTE: For maintainers to batch add data, but these extra (optional)
fields are required in the template: file, data_title.
This script is not particularly efficient nor safe, but it is not
intended for general usage: we just want to batch add some data
to the DB in the short-term.
"""

import os
import json
import logging

import subprocess

import scimodom.utils.utils as utils

from pathlib import Path
from argparse import ArgumentParser, SUPPRESS
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from functools import partial

from scimodom.config import Config
from scimodom.database.database import make_session
from scimodom.services.project import ProjectService

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


def _add_dataset(key, data, smid, directory):
    metadata = data[key]
    d = metadata[0]
    if len(metadata) > 1:
        # assume all remaining entries are identical...
        # this might not be true...
        d["rna"] = " ".join([m["rna"] for m in metadata])
        d["modomics_id"] = " ".join([m["modomics_id"] for m in metadata])
    args = [
        "add-dataset",
        "-smid",
        smid,
        "--title",
        f'"{d["data_title"]}"',
        "--file",
        Path(directory, key).as_posix(),
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
        d["tech"],
        "-cto",
        d["organism"]["cto"],
    ]
    return_code = subprocess.call(f"printf 'Y' | {' '.join(args)}", shell=True)
    return key, return_code


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
        except:
            msg = f"Failed to add project template {project['path']}. Skipping!"
            logger.error(msg)

    # add data
    for project in projects:
        smid = project.get("SMID", None)
        if smid is None:
            msg = f"Failed to add project data for {project['title']}. Skipping!"
            logger.error(msg)
            continue
        metadata = _get_dataset(project)
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as ppe:
            for key, return_code in ppe.map(
                partial(
                    _add_dataset, data=metadata, smid=smid, directory=args.directory
                ),
                metadata.keys(),
            ):
                if not return_code == 0:
                    msg = f"Failed to add dataset {key}. Skipping!"
                    logging.error(msg)


if __name__ == "__main__":
    main()
