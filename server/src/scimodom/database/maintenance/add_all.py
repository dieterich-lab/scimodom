#! /usr/bin/env python3

"""Wrapper script to add projects and dataset
from project templates (json only).

NOTE: For maintainers to batch add data, but these extra (optional)
fields are required in the template: file, data_title.
"""


import json
import logging

import scimodom.utils.utils as utils

from pathlib import Path
from argparse import ArgumentParser, SUPPRESS

from scimodom.config import Config
from scimodom.database.database import make_session


logger = logging.getLogger(__name__)

extra_cols = ["file", "data_title"]


def _get_templates(args):
    all_paths = []
    for f in args.project_template:
        path = Path(args.directory, f"{f}.json")
        if not path.is_file():
            msg = f"Template {path} missing. Skipping!"
            logger.warning(msg)
            continue
        all_paths.append(path)
    return all_paths


def _get_projects(templates):
    all_projects = []
    for template in templates:
        handle = open(template, "r")
        project = json.load(handle)
        for d in utils.to_list(project["metadata"]):
            try:
                utils.check_keys_exist(d.keys(), extra_cols)
            except:
                msg = f"Missing keys in {template} for metadata. Skipping project alltogether!"
                logger.warning(msg)
                break
        else:
            all_projects.append(project)
        handle.close()
    return all_projects


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

    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)

    templates = _get_templates(args)
    projects = _get_projects(templates)

    for project in projects:
        print(f"{project['title']}")
        # create project, get smid, create dataset/data for each entry in metadata, except
        # where an entry is for a "same" file (how to handle this case?)

    # engine, session_factory = make_session(args.database)
    # session = session_factory()
    # setup = SetupService(session)
    # setup.upsert_all()

    ## load project metadata
    # project = json.load(open(args.project))
    ## add project
    # msg = f"Adding project ({args.project}) to {args.database}..."
    # if not utils.confirm(msg):
    # return
    # ProjectService(session, project).create_project()


if __name__ == "__main__":
    main()
