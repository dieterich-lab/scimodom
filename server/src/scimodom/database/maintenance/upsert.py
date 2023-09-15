#! /usr/bin/env python3

# draft script to access the DB outside the app, ie. w/o running the app
# for loading/updating tables

# import models, session and engine from app

import sys
import argparse
import logging

import pandas as pd


# ????
import scimodom.database.models as models


from scimodom.database.database import Session, init

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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""Update DB""",
    )

    parser.add_argument(
        "-m",
        "--model",
        help="""Upsert MODEL using [--table TABLE].
                        Performs an INSERT... ON DUPLICATE KEY UPDATE. Requires [--table TABLE]""",
        type=str,
        required="--table" in sys.argv,
    )

    parser.add_argument(
        "-t",
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
    init(lambda: Session)

    if args.model:
        # qactually wdon't need model just cols, since below this goes in db...
        model = utils.get_model(args.model)

        cols = set([column.key for column in model.__table__.columns])
        table = pd.read_csv(args.table)
        table = table.loc[:, table.columns.isin(cols)]
        cols = table.columns.tolist()
        if table.shape[1] == 1:
            msg = (
                f"Only {cols[0]} found in TABLE. At least id "
                f"and one other column are required. Terminating!"
            )
            logger.error(msg)
            return
        msg = (
            f"Updating {args.model} (table {model.__table__.name}) using "
            f"the following columns: {cols}."
        )
        if not confirm(msg):
            return
        # Nan to None - check docs
        table = table.where(pd.notnull(table), None)
        values = table.to_dict(orient="records")
        with Session() as session, session.begin():
            stmt = insert(model).values(values)
            ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
            stmt = stmt.on_duplicate_key_update(**ucols)
            session.execute(stmt)

    else:
        logger.info("NOTHING")


if __name__ == "__main__":
    main()
