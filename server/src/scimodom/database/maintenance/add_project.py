#! /usr/bin/env python3

import json

from argparse import ArgumentParser, SUPPRESS
import logging

from scimodom.database.database import make_session, init

import scimodom.utils.utils as utils

from scimodom.services.project import ProjectService
from scimodom.services.setup import SetupService

logger = logging.getLogger(__name__)


def confirm(msg):
    """
    Prompt confirmation (case-insensitive).

    Parameters
    ----------
    msg
        Prompt message.

    Returns
    -------
    Bool
        True if the answer is Y/y.
    """

    answer = ""
    while answer not in ["y", "n"]:
        prompt = f"{msg}\nConfirm to continue [Y/N]? "
        answer = input(prompt).lower()
    return answer == "y"


def main():
    parser = ArgumentParser(
        add_help=False, description="""Add new project to DB - create SMID."""
    )

    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")

    required.add_argument(
        "-db", "--database", help="""Database URI""", type=str, required=True
    )

    required.add_argument(
        "-p",
        "--project",
        help="""INSERT new project using [--project PROJECT],
                          where PROJECT is a json file with required fields""",
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

    # init DB
    engine, Session = make_session(args.database)
    init(engine, lambda: Session)

    setup = SetupService(Session())
    setup.upsert_all()

    # load project metadata
    project = json.load(open(args.project))
    # add project
    msg = f"Adding project ({args.project}) to {args.database}..."
    if not confirm(msg):
        return
    ProjectService(Session(), project).create_project()


if __name__ == "__main__":
    main()
