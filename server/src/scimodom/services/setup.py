import csv
import logging
from functools import cache
from typing import Any, ClassVar

from scimodom.database.database import Base, get_session
from scimodom.database.models import (
    Annotation,
    AnnotationRelease,
    AnnotationVersion,
    Assembly,
    AssemblyVersion,
    DetectionMethod,
    Modomics,
    RNAType,
    Taxa,
    Taxonomy,
)
from scimodom.services.file import FileService, get_file_service
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SetupService:
    """Utility class to perform INSERT... ON DUPLICATE KEY UPDATE.

    :param session: SQLAlchemy ORM session
    :type session: Session | scoped_session
    """

    FILE_NAME_TO_DB_TABLE_MAP: ClassVar[dict[str, type[Base]]] = {
        "rna_type.csv": RNAType,
        "modomics.csv": Modomics,
        "taxonomy.csv": Taxonomy,
        "ncbi_taxa.csv": Taxa,
        "assembly.csv": Assembly,
        "assembly_version.csv": AssemblyVersion,
        "annotation_release.csv": AnnotationRelease,
        "annotation.csv": Annotation,
        "annotation_version.csv": AnnotationVersion,
        "method.csv": DetectionMethod,
    }
    # NOTE: the order is load-bearing, cf. upsert_all. A table must come
    # after the tables it references: annotation references assembly and
    # annotation_release.

    def __init__(self, session: Session, file_service: FileService) -> None:
        self._session = session
        self._file_service = file_service

        for name in self.FILE_NAME_TO_DB_TABLE_MAP:
            if not file_service.check_import_file(name):
                raise FileNotFoundError(f"No such file or directory: {name}")

    def is_valid_import_file(self, file_name: str) -> bool:
        """Check if import table is valid.

        :param file_name: Import table name
        :return: True is valid, else False
        """
        return file_name in self.FILE_NAME_TO_DB_TABLE_MAP

    def get_valid_import_file_names(self) -> list[str]:
        """Get allowed import table names."""
        return list(self.FILE_NAME_TO_DB_TABLE_MAP.keys())

    def upsert_all(self) -> None:
        """Upsert all tables in the configuration file."""
        for name in self.get_valid_import_file_names():
            self.upsert_one(name)

    def upsert_one(self, file_name: str) -> None:
        """Upsert one table.

        :param file_name: Table file name
        """
        model = self.FILE_NAME_TO_DB_TABLE_MAP[file_name]
        columns, records = self._get_import_file_as_records(file_name)
        self._validate_table(model, columns)
        if not records:
            logger.warning(f"No data found in {file_name}, nothing to update.")
            return
        self._bulk_upsert(model, records)

    @staticmethod
    def _convert(column: Column, value: str | None) -> Any:
        if value is None or value == "":
            return None
        if column.type.python_type is int:
            return int(value)
        return value

    @staticmethod
    def _validate_table(model: type[Base], columns: list[str]) -> None:
        name = model.__name__
        if not columns:
            # empty file, or none of the columns is a column of the table
            msg = f"TABLE {model.__tablename__} has no valid columns."
            raise Exception(msg)
        if len(columns) == 1 and not (
            name == "AssemblyVersion" or name == "AnnotationVersion"
        ):
            msg = (
                f"Only {columns[0]} found in TABLE. At least id "
                f"and one other column are required."
            )
            raise Exception(msg)
        msg = (
            f"Updating {name} (table {model.__tablename__}) using "
            f"the following columns: {columns}."
        )
        logger.debug(msg)

    def _get_import_file_as_records(
        self, name: str
    ) -> tuple[list[str], list[dict[str, Any]]]:
        model = self.FILE_NAME_TO_DB_TABLE_MAP[name]
        model_columns = {column.key: column for column in model.__table__.columns}
        with self._file_service.open_import_file(name) as fh:
            reader = csv.DictReader(fh)
            columns = [c for c in reader.fieldnames or [] if c in model_columns]
            records = [
                {c: self._convert(model_columns[c], row[c]) for c in columns}
                for row in reader
            ]
        return columns, records

    def _bulk_upsert(
        self,
        model: type[Base],
        records: list[dict[str, Any]],
    ) -> None:
        try:
            stmt = insert(model).values(records)
            ucols = {c.name: c for c in stmt.inserted}  # filter id column ?
            stmt = stmt.on_duplicate_key_update(**ucols)
            self._session.execute(stmt)
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise


@cache
def get_setup_service() -> SetupService:
    """Instantiate a SetupService object by injecting its dependencies.

    :return: Setup service instance
    """
    return SetupService(session=get_session(), file_service=get_file_service())
