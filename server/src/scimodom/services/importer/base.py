from abc import ABC, abstractmethod
import itertools
import logging
from pathlib import Path
from typing import TextIO, Iterable, ClassVar, Any

from sqlalchemy import insert
from sqlalchemy.orm import Session

import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


class MissingHeaderError(Exception):
    """Exception handling for an empty file w/ header."""

    pass


class BaseImporter(ABC):
    """Abstract base class for an importer. Reads data from
    file rowwise, buffer records, and perform bulk inserts.
    The importer is tied to a given ORM model in that it
    (1) validates the input columns against the model columns,
    and (2) insert values into the model table.

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
    :param sep: Character pattern to treat as the delimiter.
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
    :param no_flush: Imported data is flushed and committed by
    default. This parameters prevents flush and commit, allowing
    to access the records before they are eventually inserted
    into the database.
    :type no_flush: bool
    """

    class _Buffer:
        """Utility class to insert data to selected model tables.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param model: SQLAlchemy model
        :type model: Base
        :param no_flush: Imported data is flushed and committed by
        default. This parameters prevents flush and commit, allowing
        to access the records before they are eventually inserted
        into the database.
        :type no_flush: bool
        """

        MAX_BUFFER: ClassVar[int] = 1000

        def __init__(self, session: Session, model, no_flush: bool) -> None:
            """Initializer method."""
            self._session = session
            self._model = model
            self._no_flush = no_flush

            self._buffer: list[dict[str, Any]] = []

        def buffer_data(self, d: dict[str, Any]) -> None:
            """Buffers data and flush."""
            self._buffer.append(d)
            if not self._no_flush and len(self._buffer) >= self.MAX_BUFFER:
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
        model,
        sep: str,
        header: list[str] | None,
        skiprows: int = 0,
        comment: str | None = None,
        no_flush: bool = False,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._filen = filen
        self._handle = handle
        self._model = model
        self._sep = sep
        self._skiprows = skiprows
        self._no_flush = no_flush

        self._buffer: BaseImporter._Buffer
        self._dtypes: dict[str, dict[str, Any]] = dict()
        self._lino: int = skiprows
        if comment is not None and len(comment) > 1:
            raise ValueError(
                f"Maximum length of 1 expected, got {len(comment)} for comment."
            )
        self._comment = comment
        if header is None:
            self._header = self._get_header()
        else:
            self._header = header
        self._num_cols: int = len(self._header)

    @abstractmethod
    def parse_record(self, record: dict[str, str]) -> dict[str, Any]:
        """Parser. Receives a dict {column: value}, and returns a
        dict {column: value} where value is type converted. The length of
        a record is checked against that of header before calling this
        function, allowing to return additional values to be inserted
        into the model table.

        Raises ValueError(message).
        """
        pass

    def parse_records(self) -> None:
        """Import file."""
        self._validate_columns()
        self._buffer = BaseImporter._Buffer(
            session=self._session, model=self._model, no_flush=self._no_flush
        )
        for line in itertools.islice(self._handle, self._skiprows, None):
            self._lino += 1
            if self._comment is not None and not line.strip().startswith(self._comment):
                self._read_line(line)

    def close(self) -> None:
        """Close handle, flush buffer, commit."""
        self._handle.close()
        if not self._no_flush:
            self._buffer.flush()
            self._session.commit()

    def get_buffer(self) -> list[dict[str, Any]]:
        """Return buffer with records.

        :return: Buffer with records
        :rtype: list of dict of {str: Any}
        """
        return self._buffer._buffer

    def flush_records(self) -> None:
        """Force flush and commit records."""
        records = self.get_buffer()
        self._session.execute(insert(self._model), records)
        self._session.commit()

    def _get_header(self) -> list[str]:
        """Infer header from file.

        :return: Header
        :rtype: list of str
        """
        for line in itertools.islice(self._handle, self._skiprows, None):
            self._lino += 1
            if self._comment is not None and not line.strip().startswith(self._comment):
                header = [l.strip() for l in line.split(self._sep)]
                break
        # empty file...
        try:
            header
        except:
            raise MissingHeaderError(
                f"{self._filen}: Header missing. Aborting transaction!"
            )
        self._skiprows = 0
        return header

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

    def _validate(self, values: list[str]) -> dict[str, str]:
        """Format values and validate value count at row.

        :param values: Input values from line
        :type values: list of str
        :return: Formatted values
        :rtype: dict of {str: str}
        """
        num_values = len(values)
        if num_values != self._num_cols:
            raise ValueError(
                f"Column count doesn't match value count at row {self._lino}"
            )
        return {self._header[col]: values[col] for col in range(self._num_cols)}

    def _read_line(self, line: str) -> None:
        """Read a line, buffer data for insert."""
        if line.strip() == "":
            return
        # cut to header
        values = [l.strip() for l in line.split(self._sep)][: self._num_cols]
        try:
            validated = self._validate(values)
            records = self.parse_record(validated)
            self._buffer.buffer_data(records)
        except ValueError as error:
            msg = f"Skipping: Failed to parse {self._filen} at row {self._lino}: {str(error)}"
            logger.warning(msg)
