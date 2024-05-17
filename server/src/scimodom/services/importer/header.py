from pathlib import Path
import re
from typing import TextIO, Iterable, ClassVar, Any

from sqlalchemy import insert
from sqlalchemy.orm import Session

from scimodom.database.models import Dataset
import scimodom.utils.specifications as specs
import scimodom.utils.utils as utils


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


class EUFHeaderImporter:
    """Utility class to import bedRMod (EU) formatted files.
    This class specifically handles the header, cf. EUFDataImporter.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: File path
    :type filen: str
    :param handle: File handle
    :type handle: TextIO
    :param smid: Sci-ModoM project ID or SMID
    :type smid: str
    :param eufid: EUF ID (dataset) or EUFID
    :type eufid: str
    :param title: Title associated with EUF/bedRMod dataset
    :type title: str
    :param SPECS: Default specs
    :type SPECS: dict
    """

    SPECS: ClassVar[dict] = specs.SPECS_EUF

    def __init__(
        self,
        session: Session,
        filen: str,
        handle: TextIO,
        smid: str,
        eufid: str,
        title: str,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._filen = filen
        self._handle = handle
        self._smid = smid
        self._eufid = eufid
        self._title = title

        self.checkpoint = self._session.begin_nested()
        self._model = Dataset
        self._sep: str = self.SPECS["header"]["delimiter"]
        self._tag: str = self.SPECS["header"]["comment"]
        self._lino = 0

        self.taxid: int
        self.assembly: str
        self._specs_ver: str
        self._specs: dict[str, Any]
        self._required: list[str]
        self._num_cols: int
        self._dtypes: dict[str, Any]
        self._header: dict[str, Any]

        self._cast_types()

    def parse_header(self):
        """Header parser."""
        self._lino += 1
        self._read_version()
        self._parse_lines()
        self._validate_columns()

    def close(self, no_commit: bool = False) -> None:
        """Close handle, insert, and flush or commit.

        :param no_commit: Flush instead of commit
        :type no_commit: bool
        """
        self._handle.close()
        self._session.execute(insert(self._model), self._header)
        if no_commit:
            self._session.flush()
        else:
            self._session.commit()

    def _cast_types(self) -> None:
        """Cast column types for input."""
        # order of __table__.columns always the same...?
        mapped_columns = utils.get_table_columns(self._model)
        mapped_types = utils.get_table_column_python_types(self._model)
        self._dtypes = {
            c: mapped_types[mapped_columns.index(c)] for c in mapped_columns
        }

    def _read_version(self) -> None:
        """Read and validate EUF version."""
        try:
            line = next(self._handle)
        except StopIteration:
            raise EOFError(f"{self._filen}")
        self._specs_ver = ".".join(re.findall(r"\d+", line))
        if not self._specs_ver == self.SPECS["versions"][-1]:
            raise SpecsError(
                f"Unknown or outdated version {self.SPECS['format']}v{self._specs_ver}."
            )
        self._specs = self.SPECS[self._specs_ver]
        self._num_cols = len(self._specs["headers"])
        self._required = self._specs["required"][1:]

    def _parse_lines(self) -> None:
        """Read and munge header lines.
        Additional lines are ignored.
        """
        lines = []
        while self._lino < self._num_cols:
            lines.append(next(self._handle))
            self._lino += 1
        self._munge_values(lines)

    def _munge_values(self, lines: list[str]) -> None:
        """Read header lines into a dictionary, cast
        types to those required by the model.

        :param lines: Header lines
        :type lines: list of str
        """

        def _is_required(header: str, s: str) -> bool:
            """Check non-empty required header string.
            There is no content validation. Values
            for organism, assembly, annotation_source,
            and annotation_version are discarded.
            Organism and assembly are checked in
            DataService. Type casting occurs later.

            :param header: Header line
            :type header: str
            :param s: Header content
            :type s: str
            :returns: True if non-empty, else False
            :rtype: bool
            """
            skip = False
            if header in self._required and not s:
                skip = True
            return skip

        def _get_header(header: str) -> str:
            """Get and validate header tag.

            :param header: Header line
            :type header: str
            :returns: Header value for given header tag
            :rtype: str
            """
            h = f"{self._tag}{header}{self._sep}"
            s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
            if not s or _is_required(header, s[0]):
                raise SpecsError(f"Missing or misformatted header: {h}.")
            return s[0]

        headers = self._specs["headers"].copy()
        _ = headers.pop("fileformat")
        self._header = {
            v: self._dtypes[v].__call__(_get_header(k))
            for k, v in headers.items()
            if v in self._dtypes.keys()
        }
        # add model columns that are not read from the header
        self._header["id"] = self._dtypes["id"].__call__(self._eufid)
        self._header["project_id"] = self._dtypes["project_id"].__call__(self._smid)
        self._header["title"] = self._dtypes["title"].__call__(self._title)
        # unassigned, but used to validate association
        self.taxid = int(_get_header("organism"))
        self.assembly = str(_get_header("assembly"))
        # unused, but required according to EUF specs
        _ = _get_header("annotation_source")
        _ = _get_header("annotation_version")
        # for non-required headers, nullify empty strings
        self._header = dict((k, None if not v else v) for k, v in self._header.items())

    def _validate_columns(self) -> None:
        """Validate if the file has the minimum number
        of columns. This does not validate the column names,
        as there can be any number of additional rows in
        the header, only the first row without tag is validated.
        An empty first record will raise the same error.
        """
        num_cols = len(self._specs["columns"])
        cols = []
        for line in self._handle:
            self._lino += 1
            if not line.strip().startswith(self._tag):
                cols = [l.strip() for l in line.split(self.SPECS["delimiter"])]
                break
        # silently ignore extra cols
        cols = cols[:num_cols]
        if len(cols) != num_cols:
            msg = (
                f"Column count (header) doesn't match required count at row {self._lino} "
                f"for {self.SPECS['format']}v{self._specs_ver}."
            )
            raise SpecsError(msg)
