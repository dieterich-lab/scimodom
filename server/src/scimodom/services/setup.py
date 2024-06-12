import logging
from functools import cache
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore # import-untyped

from scimodom.config import Config
from scimodom.database.database import Base, get_session
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class SetupService:
    """Utility class to perform INSERT... ON DUPLICATE KEY UPDATE.

    :param session: SQLAlchemy ORM session
    :type session: Session | scoped_session
    """

    def __init__(self, session) -> None:
        """Initializer method."""
        self._session = session
        self._config = Config()
        self._models_tables = [
            self._config.rna_tbl,
            self._config.modomics_tbl,
            self._config.taxonomy_tbl,
            self._config.ncbi_taxa_tbl,
            self._config.assembly_tbl,
            self._config.assembly_version_tbl,
            self._config.annotation_tbl,
            self._config.annotation_version_tbl,
            self._config.method_tbl,
        ]

        for _, table in self._models_tables:
            if not table.is_file():
                msg = f"No such file or directory: {table.as_posix()}"
                raise FileNotFoundError(msg)

    @staticmethod
    def get_table(model: Base, table: str | Path) -> pd.DataFrame:
        """Read table, keeping only relevant columns.

        :param model: SQLAlchemy model
        :type model: Base
        :param table: Path to data table
        :type table: str | Path
        :returns: Data table
        :rtype: pd.DataFrame
        """
        cols = set([column.key for column in model.__table__.columns])
        df = pd.read_csv(table)
        df = df.loc[:, df.columns.isin(cols)]
        return df

    @staticmethod
    def validate_table(model: Base, table: pd.DataFrame) -> None:
        """Validate data table.

        :param model: SQLAlchemy model
        :type model: Base
        :param table: Path to data table
        :type table: pd.DataFrame
        """
        cols = table.columns.tolist()
        name = model.__name__
        if table.shape[1] == 1 and not (
            name == "AssemblyVersion" or name == "AnnotationVersion"
        ):
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

    def bulk_upsert(self, model, table: pd.DataFrame) -> None:
        """Perform bulk INSERT... ON DUPLICATE KEY UPDATE.

        :param model: SQLAlchemy model
        :type model: Union[TableClause, Join, Alias, CTE, type[Any], Inspectable[_HasClauseElement], _HasClauseElement]
        :param table: Path to data table
        :type table: pd.DataFrame
        """
        from sqlalchemy.dialects.mysql import insert

        # Nan to None - check docs
        table = table.where(pd.notnull(table), None)
        values = table.to_dict(orient="records")
        stmt = insert(model).values(values)
        ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
        stmt = stmt.on_duplicate_key_update(**ucols)

        self._session.execute(stmt)
        self._session.commit()

    def upsert_all(self) -> None:
        """Upsert all tables in the configuration file."""
        for m, t in self._models_tables:
            model = utils.get_model(m)
            table = self.get_table(model, t)
            self.validate_table(model, table)
            self.bulk_upsert(model, table)


@cache
def get_setup_service() -> SetupService:
    return SetupService(session=get_session())
