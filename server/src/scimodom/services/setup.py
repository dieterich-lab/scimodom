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
        # the order matters!
        self._tables = [
            self._config.modomics_tbl,
            self._config.taxonomy_tbl,
            self._config.ncbi_taxa_tbl,
            self._config.assembly_tbl,
            self._config.assembly_version_tbl,
            self._config.method_tbl,
        ]
        self._models = [
            "Modomics",
            "Taxonomy",
            "Taxa",
            "Assembly",
            "AssemblyVersion",
            "DetectionMethod",
        ]

    # to importer class...

    def get_table(self, model, table):
        cols = set([column.key for column in model.__table__.columns])
        table = pd.read_csv(table)
        table = table.loc[:, table.columns.isin(cols)]
        return table

    def validate_table(self, model, table):
        cols = table.columns.tolist()
        name = model.__name__
        if table.shape[1] == 1 and not name == "AssemblyVersion":
            msg = (
                f"Only {cols[0]} found in TABLE. At least id "
                f"and one other column are required. Terminating!"
            )
            raise Exception(msg)
        msg = (
            f"Updating {name} (table {model.__table__.name}) using "
            f"the following columns: {cols}."
        )
        logger.debug(msg)

    def bulk_upsert(self, model, table):
        from sqlalchemy.dialects.mysql import insert

        # Nan to None - check docs
        table = table.where(pd.notnull(table), None)
        values = table.to_dict(orient="records")
        stmt = insert(model).values(values)
        ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
        stmt = stmt.on_duplicate_key_update(**ucols)

        self._session.execute(stmt)
        self._session.commit()

    def upsert_all(self):
        for m, t in zip(self._models, self._tables):
            model = utils.get_model(m)
            table = self.get_table(model, t)
            self.validate_table(model, table)
            self.bulk_upsert(model, table)

    # TODO: upsert selected tables from DB (version) dump
