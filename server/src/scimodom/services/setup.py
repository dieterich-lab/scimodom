import logging
from functools import cache

import pandas as pd  # type: ignore # import-untyped
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from scimodom.database.database import Base, get_session
from scimodom.database.models import (
    RNAType,
    Modomics,
    Taxonomy,
    Taxa,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    DetectionMethod,
)
from scimodom.services.file import FileService, get_file_service

logger = logging.getLogger(__name__)


class SetupService:
    """Utility class to perform INSERT... ON DUPLICATE KEY UPDATE.

    :param session: SQLAlchemy ORM session
    :type session: Session | scoped_session
    """

    def __init__(self, session: Session, file_service: FileService) -> None:
        self._session = session
        self._file_service = file_service

        # Should that matter here? Or should we only worry on demand?
        for name in self.FILE_NAME_TO_DB_TABLE_MAP.keys():
            if not file_service.check_import_file(name):
                raise FileNotFoundError(f"No such file or directory: {name}")

    FILE_NAME_TO_DB_TABLE_MAP = {
        "rna_type.csv": RNAType,
        "modomics.csv": Modomics,
        "taxonomy.csv": Taxonomy,
        "ncbi_taxa.csv": Taxa,
        "assembly.csv": Assembly,
        "assembly_version.csv": AssemblyVersion,
        "annotation.csv": Annotation,
        "annotation_version.csv": AnnotationVersion,
        "method.csv": DetectionMethod,
    }

    def upsert_one(self, file_name: str):
        model = self.FILE_NAME_TO_DB_TABLE_MAP[file_name]
        data = self._get_import_file_as_dataframe(file_name)
        self._validate_table(model, data)
        self._bulk_upsert(model, data)

    def _get_import_file_as_dataframe(self, name: str) -> pd.DataFrame:
        """Read table, keeping only relevant columns.

        :param name: Name of the file to import
        :type name: str
        :returns: Data table
        :rtype: pd.DataFrame
        """
        model = self.FILE_NAME_TO_DB_TABLE_MAP[name]
        cols = set([column.key for column in model.__table__.columns])
        with self._file_service.open_import_file(name) as fh:
            df = pd.read_csv(fh)
        df = df.loc[:, df.columns.isin(cols)]
        return df

    @staticmethod
    def _validate_table(model: Base, table: pd.DataFrame) -> None:
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

    def _bulk_upsert(self, model, table: pd.DataFrame) -> None:
        """Perform bulk INSERT... ON DUPLICATE KEY UPDATE.

        :param model: SQLAlchemy model
        :type model: Union[TableClause, Join, Alias, CTE, type[Any], Inspectable[_HasClauseElement], _HasClauseElement]
        :param table: Path to data table
        :type table: pd.DataFrame
        """
        try:
            # Nan to None - check docs
            table = table.where(pd.notnull(table), None)
            values = table.to_dict(orient="records")
            stmt = insert(model).values(values)
            ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
            stmt = stmt.on_duplicate_key_update(**ucols)
            self._session.execute(stmt)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def upsert_all(self) -> None:
        """Upsert all tables in the configuration file."""
        for name in self.FILE_NAME_TO_DB_TABLE_MAP.keys():
            self.upsert_one(name)

    def is_valid_import_file(self, file_name: str) -> bool:
        return file_name in self.FILE_NAME_TO_DB_TABLE_MAP.keys()

    def get_valid_import_file_names(self) -> list[str]:
        return list(self.FILE_NAME_TO_DB_TABLE_MAP.keys())

    def get_upsert_message(self, file_name: str) -> str:
        model = self.FILE_NAME_TO_DB_TABLE_MAP[file_name]
        return (
            f"Updating {model.__name__} (table {model.__table__.name}) using "
            f"the following columns: {model.columns.tolist()}."
        )


@cache
def get_setup_service() -> SetupService:
    return SetupService(session=get_session(), file_service=get_file_service())
