#! /usr/bin/env python3

# draft script to access the DB outside the app, ie. w/o running the app
# for loading/updating tables

import sys
from argparse import ArgumentParser, SUPPRESS
import logging

import pandas as pd

from scimodom.database.database import make_session, init

from scimodom.services.setup import SetupService

import scimodom.utils.utils as utils


from sqlalchemy.dialects.mysql import insert

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

    utils.add_log_opts(parser)
    args = parser.parse_args()
    utils.update_logging(args)

    # init DB
    logger.info(f"Creating schema for {args.database}...")
    engine, Session = make_session(args.database)
    init(engine, lambda: Session)

    # upsert one table
    # or upset all path to import directory
    # dump

    setup = SetupService(Session)

    # if # upsert one table

    # model = utils.get_model(args.model)
    # values, msg = setup.get_values(model, args.table)
    # if not confirm(msg):
    # return

    # setup.bulk_upsert(model, values)

    # else if # uspert all

    # setup.upsert_all()

    # else # pass

    # if args.model:
    # try:
    # model = utils.get_model(args.model)
    # except KeyError as error:
    # msg = f"Model undefined: {args.model}. Terminating!"
    # logger.error(msg)
    # raise KeyError(error)
    # cols = set([column.key for column in model.__table__.columns])
    # table = pd.read_csv(args.table)
    # table = table.loc[:, table.columns.isin(cols)]
    # cols = table.columns.tolist()
    # if table.shape[1] == 1:
    # msg = (
    # f"Only {cols[0]} found in TABLE. At least id "
    # f"and one other column are required. Terminating!"
    # )
    # logger.error(msg)
    # return
    # msg = (
    # f"Updating {args.model} (table {model.__table__.name}) using "
    # f"the following columns: {cols}."
    # )
    # if not confirm(msg):
    # return
    ## Nan to None - check docs
    # table = table.where(pd.notnull(table), None)
    # values = table.to_dict(orient="records")
    # with Session() as session, session.begin():
    # stmt = insert(model).values(values)
    # ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
    # stmt = stmt.on_duplicate_key_update(**ucols)
    # session.execute(stmt)


if __name__ == "__main__":
    main()
