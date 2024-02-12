from abc import ABC, abstractmethod
import itertools
import logging
from pathlib import Path
from typing import TextIO, Iterable, ClassVar, Any

from sqlalchemy import insert
from sqlalchemy.orm import Session


from scimodom.database.database import Base
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class MissingHeaderError(Exception):
    """Exception handling for an empty file w/ header."""

    pass


class BaseImporter(ABC):
    """Abstract base class for an importer. Reads data from
    file rowwise, buffer records, and perform bulk inserts.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: File path
    :type filen: str
    :param handle: File handle
    :type handle: TextIO
    :param model: SQLAlchemy ORM model
    :type model: Base
    :param header: Model columns to use as header (default).
    If the file contains a header, use skiprows and/or comment.
    If header is None, column names are inferred and must match
    the corresponding model columns.
    :type header: Sequence of str | None
    :param sep: Delimiter
    :type sep: str
    :param skiprows: Number of lines to skip at the start of the
    file. If header is None (infer), the first line that is not
    skipped and not a comment is used as a header.
    :type skiprows: int
    :param comment: Character indicating that the line should
    not be parsed. This parameter must be a single character. Only
    comments starting a line are considered. The line is ignored
    alltogether. Commented lines are not ignored by skiprows (see
    parameter skiprows).
    :type comment: str | None
    """

    class _Buffer:
        """Utility class to insert data to selected model tables.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param model: SQLAlchemy model
        :type model: Base
        """

        MAX_BUFFER: ClassVar[int] = 1000

        def __init__(self, session: Session, model: Base) -> None:
            """Initializer method."""
            self._session = session
            self._model = model
            self._buffer: list = []

        def buffer_data(self, d: dict[str | Any]) -> None:
            """Buffers data and flush."""
            self._buffer.append(d)
            if len(self._buffer) >= self.MAX_BUFFER:
                self.flush()

        def flush(self) -> None:
            """Insert and reset buffer."""
            if not self._buffer:
                return
            self._session.execute(insert(self._model), self._buffer)
            self._buffer = []

    def __init__(
        self,
        session: Session,
        filen: str,
        handle: TextIO,
        model: Base,
        header: list[str] | None,
        sep: str,
        skiprows: int = 0,
        comment: str | None = None,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._filen = filen
        self._handle = handle
        self._model = model
        self._header = header
        self._sep = sep
        self._skiprows = skiprows
        self._comment = comment

        self._lino: int
        self._num_cols: int
        self._buffer: BaseImporter._Buffer
        self._dtypes: dict[str, dict[str, Any]] = dict()

    @abstractmethod
    def parse_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Parser. Receives a dict {column: value}, and returns a
        dict {column: value} where value is type converted. Length of
        records are checked before calling this function, allowing to
        return additional values to be inserted into the model table.

        Raises ValueError(message).
        """
        pass

    def parse_records(self):
        """Import file."""
        self._lino = self._skiprows
        if self._header is None:
            self._get_header()
        self._validate_columns()
        self._num_cols = len(self._header)
        self._buffer = BaseImporter._Buffer(session=self._session, model=self._model)
        for line in itertools.islice(self._handle, self._skiprows, None):
            self._lino += 1
            if not self._comment.startswith(line):
                self._read_line(line)

    def _get_header(self):
        """Infer header from file."""
        for line in itertools.islice(self._handle, self._skiprows, None):
            self._lino += 1
            if not self._comment.startswith(line):
                self._header = [l.strip() for l in line.split(self._sep)]
                break
        # empty file...
        if self._header is None:
            raise MissingHeaderError(
                f"{self._file}: Header missing. Aborting transaction!"
            )
        self._skiprows = 0

    def _validate_columns(self) -> None:
        """Validate model attributes."""
        # assume order of __table__.columns is consistent...
        mapped_columns = utils.get_table_columns(self._model)
        for c in self._header:
            if c not in mapped_columns:
                msg = (
                    f"Column name {c} doesn't match any of the ORM mapped attribute names "
                    f"for {self._model.__name__}. This can be caused by a file header with wrong "
                    "column names, or a change in model declaration. Aborting transaction!"
                )
                raise Exception(msg)

    def _read_line(self, line: str) -> None:
        """Read a line, buffer data for insert."""
        if line.strip() == "":
            return
        values = [l.strip() for l in line.split(self._sep)]
        try:
            validated = self._validate(values)
            records = self.parse_record(validated)
            self._buffer.buffer_data(records)
        except ValueError as error:
            msg = f"Warning: Failed to parse {self._filen} at row {self._lino}: {str(error)} - skipping!"
            logger.warning(msg)

    def _validate(self, values: list[str]) -> list[str]:
        """Validate value count at row."""
        num_values = len(values)
        if num_values != self._num_cols:
            raise ValueError(
                f"Column count doesn't match value count at row {self._lino}"
            )
        return {self._header[col]: values[col] for col in range(self._num_cols)}

    def close(self) -> None:
        """Close handle, flush buffer, commit."""
        self._handle.close()
        self._buffer.flush()
        self._session.commit()
