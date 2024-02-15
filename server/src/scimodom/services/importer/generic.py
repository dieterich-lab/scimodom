from typing import TextIO, ClassVar, Any

from sqlalchemy.orm import Session

from scimodom.database.models import Data
from scimodom.services.importer.base import BaseImporter
import scimodom.utils.utils as utils


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


class BEDImporter(BaseImporter):
    """Utility class to import BED formatted files.
    BED6+ files, incl. bedRMod (EUF) are cut down to BED6.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: File path
    :type filen: str
    :param handle: File handle
    :type handle: TextIO
    """

    COLS: ClassVar[list[str]] = ["chrom", "start", "end", "name", "score", "strand"]
    SEP: ClassVar[str] = "\t"
    COMMENT: ClassVar[str] = "#"

    def __init__(
        self,
        session: Session,
        filen: str,
        handle: TextIO,
    ) -> None:
        """Initializer method."""

        self._session = session
        self._filen = filen
        self._handle = handle

        self._model = Data

        self._dtypes: dict[str, Any]
        self._itypes: list[str]

        super().__init__(
            session=session,
            filen=filen,
            handle=handle,
            model=self._model,
            sep=self.SEP,
            header=self.COLS,
            comment=self.COMMENT,
            no_flush=True,
        )

        self._cast_types()

    def parse_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Data parser.

        :param record: A data record (line) as a dictionary
        :type record: dict of {str: str}
        :return: A data record as a dictionary, with value
        typecasted to that required by the model.
        :rtype: dict of {str: Any}
        """

        # cast to float numerical types, to avoid ValueError for
        # non "integer-like" input records. NOTE: data loss may occur!
        frecord = {k: float(v) if k in self._itypes else v for k, v in record.items()}
        crecord = {k: self._dtypes[k].__call__(v) for k, v in frecord.items()}
        # no validation - leave out to pybedtools
        return crecord

    def _cast_types(self) -> None:
        """Cast column types for input, using Data model."""
        # order of __table__.columns always the same...?
        mapped_columns = utils.get_table_columns(self._model)
        mapped_types = utils.get_table_column_python_types(self._model)
        self._dtypes = {
            c: mapped_types[mapped_columns.index(c)]
            for c in mapped_columns
            if c in self.COLS
        }
        self._itypes = [k for k, v in self._dtypes.items() if v.__name__ == "int"]
