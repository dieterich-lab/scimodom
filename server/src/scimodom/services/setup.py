#! /usr/bin/env python3


import pandas as pd

import logging

logger = logging.getLogger(__name__)

import scimodom.utils.utils as utils
from scimodom.config import Config


class SetupService:
    def __init__(self, session):
        self._session = session
        self._config = Config()
        self._tables = [
            self._config.modomics_tbl,
            self._config.assembly_tbl,
            self._config.taxonomy_tbl,
            self._config.ncbi_taxa_tbl,
        ]
        self._models = [
            "Modomics",
            "Assembly",
            "Taxonomy",
            "Taxa",
        ]

    # to importer class...

    def get_values(model, table):
        cols = set([column.key for column in model.__table__.columns])
        table = pd.read_csv(table)
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
            f"Updating {model.__name__} (table {model.__table__.name}) using "
            f"the following columns: {cols}."
        )

        table = table.where(pd.notnull(table), None)
        values = table.to_dict(orient="records")

        return values, msg

    def bulk_upsert(self, model, values):
        from sqlalchemy.dialects.mysql import insert

        stmt = insert(model).values(values)
        ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
        stmt = stmt.on_duplicate_key_update(**ucols)

        self._session.execute(stmt)
        self._session.commit()

    def upsert_all(self):
        # model = utils.get_model(model_str)

        for model_str, table in zip(self._models, self._tables):
            print(f"MODEL {model_str}, TABLE {table}")
            model = utils.get_model(model_str)
            values, msg = self.get_values(model, table)
            logger.info(msg)
