#! /usr/bin/env python3


import pandas as pd

import logging

logger = logging.getLogger(__name__)

import scimodom.utils.utils as utils


class SetupService:
    def __init__(self, session, project, config):
        self._session = session
        self._project = project
        self._config = config

    def get_values(model_str, table_path):
        model = utils.get_model(model_str)
        cols = set([column.key for column in model.__table__.columns])
        table = pd.read_csv(table_path)
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
            f"Updating {model_str} (table {model.__table__.name}) using "
            f"the following columns: {cols}."
        )
        table = table.where(pd.notnull(table), None)
        values = table.to_dict(orient="records")
        return values, msg

    # def bulk_upsert():
    # one upsert - e.g. call in upsert maintenance one by one

    # def upsert_all():
    # call from the app, uspsert all tables calling bulk_upsert - use config - define models (here)
