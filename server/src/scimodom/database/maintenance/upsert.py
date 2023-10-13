#! /usr/bin/env python3

"""Maintenance script for the SetupService utility.
This script allows to upsert selected or all DB tables.
"""

import sys
import logging

import scimodom.utils.utils as utils

from argparse import ArgumentParser, SUPPRESS
from scimodom.database.database import make_session, init
from scimodom.services.setup import SetupService

logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser(
        add_help=False,
        description="""Upsert selected DB tables. With [-db/--database] only,
        init database schema.""",
    )

    required = parser.add_argument_group("required arguments")
    optional = parser.add_argument_group("optional arguments")

    required.add_argument(
        "-db", "--database", help="""Database URI""", type=str, required=True
    )

    optional.add_argument(
        "-h",
        "--help",
        help="show this help message and exit",
        action="help",
        default=SUPPRESS,
    )

    optional.add_argument(
        "--model",
        help="""Upsert MODEL using [--table TABLE].
                        Performs an INSERT... ON DUPLICATE KEY UPDATE. Requires [--table TABLE]""",
        type=str,
        required="--table" in sys.argv,
    )

    optional.add_argument(
        "--table",
        help="""Database table for MODEL with column
                        names. Only columns matching __table__.columns are used.
                        CSV format. Requires [--model MODEL]""",
        type=str,
        required="--model" in sys.argv,
    )

    optional.add_argument(
        "--all",
        help="""Default upsert all tables defined in config.py. Overrides [--model/--table].""",
        action="store_true",
    )

    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)

    # init DB
    logger.info(f"Creating schema for {args.database}...")
    engine, Session = make_session(args.database)
    init(engine, lambda: Session)

    setup = SetupService(Session())

    if args.all:
        setup.upsert_all()
    elif args.model:
        model = utils.get_model(args.model)
        table = setup.get_table(model, args.table)
        setup.validate_table(model, table)
        msg = (
            f"Updating {model.__name__} (table {model.__table__.name}) using "
            f"the following columns: {table.columns.tolist()}."
        )
        if not utils.confirm(msg):
            return
        setup.bulk_upsert(model, table)
    else:
        pass


if __name__ == "__main__":
    main()
