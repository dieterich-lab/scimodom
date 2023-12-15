#! /usr/bin/env python3

import re
import logging
import itertools

import scimodom.utils.utils as utils
import scimodom.database.queries as queries
import scimodom.utils.specifications as specs

from pathlib import Path
from typing import TextIO, Iterable, ClassVar, Any
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from scimodom.config import Config
from scimodom.services.annotation import AnnotationService
from scimodom.database.models import Data, Dataset
from scimodom.database.database import Base

logger = logging.getLogger(__name__)

# if needed
# from abc import ABC, abstractmethod
# BaseImporter(ABC):
#   @abstractmethod
#   def parse(self, data):
# then define given importer e.g. MyImporter(BaseImporter)


# ad hoc wrangling of annotation_source and annotation_version
# according to EUF specs, entries are required, but often they are just None
# we allow them to be nullable
empty_pattern = re.compile(
    ".*?missing.*?|.*?unknown.*?|nothing|none|no.*?|null|nan|na|nil", re.I
)

# ad hoc wrangling of chrom field
chrom_pattern = re.compile("chromosome|chrom|chr", re.I)


class SpecsError(Exception):
    """Exception handling for specification errors."""

    pass


class EUFImporter:
    """Utility class to read data from bedRMod format
    and write to database tables.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: EUF/bedRMod file path/name
    :type filen: str
    :param handle: EUF/bedRMod file handle
    :type handle: TextIO
    :param smid: SMID
    :type smid: str
    :param eufid: EUFID
    :type eufid: str
    :param title: Title associated with EUF/bedRMod file/dataset
    :type title: str
    :param taxa_id: Taxonomy ID (organism) for file/dataset
    :type taxa_id: int
    :param assembly_id: Assembly ID for file/dataset (given at upload, not from file header)
    :type assembly_id: int
    :param lifted: Is Assembly ID (version) different from DB assembly version? (dataset marked for liftover)
    :type lifted: bool
    :param data_path: DATA_PATH (AnnotationService)
    :type data_path: str | Path | None
    :param SPECS: Default specs
    :type SPECS: dict
    """

    SPECS: ClassVar[dict] = specs.SPECS_EUF

    class _Buffer:
        """Utility class to insert data to selected model tables.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param model: SQLAlchemy model
        :type model: Base
        """

        MAX_BUFFER: ClassVar[int] = 1000

        def __init__(self, session: Session, model) -> None:
            """Initializer method."""
            self._session = session
            self._model = model
            self._buffer: list[dict] = []

        def buffer_data(self, d: dict) -> None:
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
        smid: str,
        eufid: str,
        title: str,
        taxa_id: int,
        assembly_id: int,
        lifted: bool,
        data_path: str | Path | None = None,
    ) -> None:
        """Initializer method."""
        self._sep: str = self.SPECS["delimiter"]
        self._htag: str = self.SPECS["header"]["comment"]
        self._hsep: str = self.SPECS["header"]["delimiter"]
        self._hrequired: list[str]
        self._version: str | None = None
        self._specs: dict
        self._int_types: list

        self._lino: int
        self._header: dict[str, Any]
        self._buffers: dict[str, EUFImporter._Buffer] = dict()
        self._dtypes: dict[str, dict[str, Any]] = dict()
        self._modifications_from_file: set[str] = set()
        self._chroms: list[str] = []

        # presumably, SMID, title, taxa_id, assembly_id all come from the FE upload form
        # or from arguments to the API/maintenance -> TODO: data upload service
        # there we should check if SMID, taxa_id, and assembly_id are valid choices
        # here, we assume they are already checked
        self._session = session
        self._filen = filen
        self._handle = handle
        self._smid = smid
        self._eufid = eufid
        self._title = title
        self._taxa_id = taxa_id
        self._assembly_id = assembly_id
        self._lifted = lifted
        self._data_path = data_path

        if self._data_path is None:
            self._data_path = Config.DATA_PATH

    def close(self) -> None:
        """Close handle, flush all buffers, commit."""
        self._handle.close()
        for _buffer in self._buffers.values():
            _buffer.flush()
        self._session.commit()

    def parseEUF(self) -> None:
        """File parser."""
        if not self._chroms:
            self._get_chroms()
        self._lino = 1
        self._read_version()
        self._validate_attributes(Dataset, self._specs["headers"].values())
        self._validate_attributes(Data, self._specs["columns"].values())
        self._buffers["Dataset"] = EUFImporter._Buffer(
            session=self._session, model=Dataset
        )
        self._read_header()
        self._buffers["Data"] = EUFImporter._Buffer(session=self._session, model=Data)
        data_line = self._lino
        for line in itertools.islice(self._handle, data_line, None):
            self._lino += 1
            self._read_line(line)

    def _get_chroms(self):
        """Read chrom.sizes."""
        query = queries.query_column_where(
            "Taxa",
            "name",
            filters={"id": self._taxa_id},
        )
        organism = self._session.execute(query).scalar()
        organism = "_".join(organism.split())

        query = queries.query_column_where(
            "Assembly", "name", filters={"id": self._assembly_id}
        )
        assembly = self._session.execute(query).scalar()

        parent, chrom_file = AnnotationService.get_chrom_path(
            self._data_path, organism, assembly
        )
        destination = Path(parent, chrom_file)
        with open(destination, "r") as f:
            lines = f.readlines()
        self._chroms = [l.split()[0] for l in lines]

    def _read_version(self) -> None:
        """Read and validate EUF/bedRMod version."""
        try:
            line = next(self._handle)
        except StopIteration:
            raise EOFError(f" {self._filen}")
        version = ".".join(re.findall(r"\d+", line))
        try:
            self._version = f"{self.SPECS['format']}v{version}"
            self._specs = self.SPECS[version]
            self._hrequired = self._specs["required"][1:]
        except KeyError:
            raise SpecsError(f" Unknown version: {self._version}.")

    def _validate_attributes(self, model, specs: Iterable[str]) -> None:
        """Validate specifications against model attributes.

        :param model: SQLAlchemy model or name of model
        :type model: Base | str
        :param specs: Header specifications (column names)
        :type specs: Iterable
        """
        # assume order of __table__.columns is consistent...
        mapped_columns = utils.get_table_columns(model)
        mapped_types = utils.get_table_column_python_types(model)
        _dtypes = dict()
        for c in specs:
            if c not in mapped_columns:
                msg = (
                    f"Column name {c} doesn't match any of the ORM mapped attribute names "
                    f"for {model.__name__}. This is likely due to a change in model declaration."
                )
                raise Exception(msg)
            idx = mapped_columns.index(c)
            _dtypes[c] = mapped_types[idx]
        self._dtypes[model.__name__] = _dtypes

    def _add_missing_header_fields(self, assembly: str) -> None:
        """Add all fields required to update model.

        :param assembly: Assembly header information
        "type assembly: str
        """
        self._header["id"] = self._eufid
        self._header["project_id"] = self._smid
        self._header["title"] = self._title
        self._header["file_format"] = self._version
        if not self._header["taxa_id"] == self._taxa_id:
            msg = (
                f"Organism={self._header['taxa_id']} from {self._filen} differs "
                f"from {self._taxa_id} given at upload. Overwriting header."
                f"Data import will continue with {self._taxa_id}..."
            )
            logger.warning(msg)
            self._header["taxa_id"] = self._taxa_id
        query = queries.query_column_where(
            "Assembly", "name", filters={"id": self._assembly_id}
        )
        assembly_name = self._session.execute(query).scalar()
        msg = (
            f"Overwriting header: assembly={assembly} from {self._filen} "
            f"with {assembly_name} given at upload. Data import will continue..."
        )
        logger.warning(msg)
        # assign id now
        self._header["assembly_id"] = self._assembly_id
        self._header["lifted"] = self._lifted

    def _munge_header(self, lines: list[str]) -> str:
        """Read header into dictionary, cast types to those required by the model.

        :param lines: Header lines
        :type lines: list
        :returns: Assembly header information
        :rtype: str
        """

        def _is_required(header: str, s: str) -> bool:
            """Check if required header is not empty.

            Note: We cannot check content, just if string
            is not empty. Type casting occurs later.

            :param header: Header line
            :type header: str
            :param s: Header content
            :type s: str
            :returns: True if non-empty, else False
            :rtype: bool
            """
            skip = False
            if header in self._hrequired and not s:
                skip = True
            return skip

        def _get_header(header: str) -> str:
            """Get and validate header tag.

            :param header: Header line
            :type header: str
            :returns: Header value for given header tag
            :rtype: str
            """
            h = f"{self._htag}{header}{self._hsep}"
            s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
            if not s or _is_required(header, s[0]):
                raise SpecsError(f" Missing or misformatted header: {h} ")
            return s[0]

        skip_header = ["fileformat", "assembly"]
        self._header = {
            mapped_header: self._dtypes["Dataset"][mapped_header].__call__(
                _get_header(header)
            )
            for (header, mapped_header) in self._specs["headers"].items()
            if header not in skip_header
        }
        # for non-required headers, nullify empty strings
        self._header = dict((k, None if not v else v) for k, v in self._header.items())
        # ad hoc wrangling of annotation_source, annotation_version
        if empty_pattern.match(self._header["annotation_source"]):
            self._header["annotation_source"] = None
        if empty_pattern.match(self._header["annotation_version"]):
            self._header["annotation_version"] = None
        return _get_header("assembly")

    def _read_header(self) -> None:
        """Read header."""
        # or do reverse search, line by line ...?
        lines = []
        while self._lino < len(self._specs["headers"]):
            lines.append(next(self._handle))
            self._lino += 1
        assembly = self._munge_header(lines)
        self._add_missing_header_fields(assembly)
        _buffer = self._buffers["Dataset"]
        _buffer.buffer_data(self._header)
        _buffer.flush()

        # read remaining header lines that are unused
        for line in self._handle:
            self._lino += 1
            if not line.strip().startswith(self._htag):
                self._validate_columns(line)
                self._lino -= 1
                break
        self._handle.seek(0)

    # def _validate_columns(self) -> None:
    # """Validate bedRMod/EUF columns

    # Note: This function forces standard column names!
    # """
    # num_cols = len(self._specs["columns"])
    # line = next(self._handle).replace(self._htag, "")
    # self._lino += 1
    # cols = [l.strip() for l in line.split(self._sep)]
    # extra_cols = cols[num_cols:]
    # for col in extra_cols:
    # msg = f"Extra column '{col}' from {self._filen} will be ignored."
    # logger.warning(msg)
    # cols = cols[:num_cols]
    # if len(cols) != num_cols:
    # msg = f"Column count doesn't match required count at row {self._lino} for {self._version}."
    # raise SpecsError(msg)
    ## Is it safe? How to overwrite if this happens (EUFID assignment, etc.)?
    # for col_read, col_specs in zip(cols, self._specs["columns"].keys()):
    # if not col_read.lower() == col_specs.lower():
    # msg = (
    # f"Column name '{col_read}' from {self._filen} differs from the required {col_specs}. "
    # f"Data import will continue, assuming conformity to {self._version}. "
    # f"If you suspect misformatting, or data corruption, check {self._filen} and start again!"
    # )
    # logger.warning(msg)
    ## for type casting
    # self._int_types = [
    # i
    # for i, v in enumerate(self._specs["columns"].values())
    # if v
    # in [
    # "start",
    # "end",
    # "score",
    # "thick_start",
    # "thick_end",
    # "coverage",
    # "frequency",
    # ]
    # ]

    def _validate_columns(self, line) -> None:
        """Validate bedRMod/EUF columns"""
        num_cols = len(self._specs["columns"])
        cols = [l.strip() for l in line.split(self._sep)]
        # silently ignore extra cols
        cols = cols[:num_cols]
        if len(cols) != num_cols:
            msg = f"Column count doesn't match required count at row {self._lino} for {self._version}."
            raise SpecsError(msg)
        # for type casting
        self._int_types = [
            i
            for i, v in enumerate(self._specs["columns"].values())
            if v
            in [
                "start",
                "end",
                "score",
                "thick_start",
                "thick_end",
                "coverage",
                "frequency",
            ]
        ]

    def _munge_values(self, values: list[str]) -> dict:
        """Read data records into dictionary, cast types to those required by the model.

        :param values: Records for one line
        :type lines: list
        :returns: Records as a dict
        :rtype: dict
        """
        num_values = len(values)
        num_cols = len(self._specs["columns"])
        if num_values != num_cols:
            raise ValueError(
                f"Column count doesn't match value count at row {self._lino}"
            )
        # first cast to float all numerical types, then type cast model (int or float)
        # NOTE: data loss may occur if e.g. coverage or frequency are wrongly assumed to be float
        cvalues = [
            float(v) if i in self._int_types else v for i, v in enumerate(values)
        ]
        data = {
            c: self._dtypes["Data"][c].__call__(cvalues[i])
            for i, c in enumerate(self._specs["columns"].values())
        }
        data["dataset_id"] = self._eufid
        # format chrom field
        match = chrom_pattern.match(data["chrom"])
        if match:
            data["chrom"] = data["chrom"].replace(match.group(), "")
        # throw away contigs
        if not data["chrom"] in self._chroms:
            raise ValueError(
                f"Skipping chrom {data['chrom']} at line {self._lino}. You can safely ignore "
                "this warning for scaffolds and contigs, otherwise this could be due to misformatting!"
            )
        # additional checks...
        if not data["strand"] in ["+", "-"]:
            raise ValueError(
                f"Unknown strand {data['strand']}! Skipping entry at line {self._lino}!"
            )
        return data

    def _read_line(self, line: str) -> None:
        """Read a line, buffer data for insert."""
        values = [l.strip() for l in line.split(self._sep)]
        try:
            validated_values = self._munge_values(values)
            self._modifications_from_file.add(validated_values["name"])
            self._buffers["Data"].buffer_data(validated_values)
        except ValueError as error:
            msg = f"Warning: Failed to parse {self._filen} at row {self._lino}: {error} - skipping!"
            logger.warning(msg)

    def get_modifications_from_file(self) -> set[str]:
        """Store all modifications found in a EUF/bedRMod file (column "name")

        :returns: Modifications as recorded in file
        :rtype: set
        """
        return self._modifications_from_file


class BEDImporter:
    """Utility class to read data from BED format
    and return as records.

    NOTE: WIP only BED6 or BED11, ignore header.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param filen: EUF/bedRMod file path/name
    :type filen: str
    :param handle: EUF/bedRMod file handle
    :type handle: TextIO
    :param smid: SMID
    :type smid: str
    :param eufid: EUFID
    :type eufid: str
    :param title: Title associated with EUF/bedRMod file/dataset
    :type title: str
    :param taxa_id: Taxonomy ID (organism) for file/dataset
    :type taxa_id: int
    :param assembly_id: Assembly ID for file/dataset (given at upload, not from file header)
    :type assembly_id: int
    :param lifted: Is Assembly ID (version) different from DB assembly version? (dataset marked for liftover)
    :type lifted: bool
    :param SPECS: Default specs
    :type SPECS: dict
    """

    SPECS: ClassVar[dict] = specs.SPECS_EUF
    QORDER: list[str] = [
        "chrom",
        "start",
        "end",
        "name",
        "score",
        "strand",
        "dataset_id",
        "coverage",
        "frequency",
    ]

    def __init__(
        self,
        filen: str,
        handle: TextIO,
        dataset_id: str,
        version: str,
    ) -> None:
        """Constructor method."""
        self._sep: str = self.SPECS["delimiter"]
        self._htag: str = self.SPECS["header"]["comment"]
        self._specs: dict
        self._int_types: list
        self._num_col: int
        self._lino: int
        self._dtypes: dict[str, dict[str, Any]] = dict()
        self._records: list = []

        self._filen = filen
        self._handle = handle
        self._dataset_id = dataset_id
        self._version = version

    def get_records(self) -> list:
        """Validate, parse, and return "as records"

        :returns: records
        :rtype: list
        """
        self.parseBED()
        self.close()
        return [tuple(d.values()) for d in self._records]

    def close(self) -> None:
        """Close handle"""
        self._handle.close()

    def parseBED(self) -> None:
        """File parser"""

        self._lino = 1
        self._read_version()

        self._validate_attributes(Data, self._specs["columns"].values())

        self._read_header()

        for line in itertools.islice(self._handle, self._lino, None):
            self._read_line(line)

    def _read_version(self) -> None:
        """Read and validate EUF/bedRMod version."""
        try:
            self._specs = self.SPECS[self._version]
        except KeyError:
            raise SpecsError(f" Unknown version: {self._version}.")

    def _validate_attributes(self, model, specs: Iterable[str]) -> None:
        """Validate specifications against model attributes.

        :param model: SQLAlchemy model or name of model
        :type model: Base | str
        :param specs: Header specifications (column names)
        :type specs: Iterable
        """
        # assume order of __table__.columns is consistent...
        mapped_columns = utils.get_table_columns(model)
        mapped_types = utils.get_table_column_python_types(model)
        _dtypes = dict()
        for c in specs:
            if c not in mapped_columns:
                msg = (
                    f"Column name {c} doesn't match any of the ORM mapped attribute names "
                    f"for {model.__name__}. This is likely due to a change in model declaration."
                )
                raise Exception(msg)
            idx = mapped_columns.index(c)
            _dtypes[c] = mapped_types[idx]
        self._dtypes[model.__name__] = _dtypes

    def _read_header(self) -> None:
        """Read header."""
        for line in self._handle:
            self._lino += 1
            if not line.startswith(self._htag):
                self._validate_columns(line)
                self._lino -= 1
                break
        self._handle.seek(0)

    def _validate_columns(self, line) -> None:
        """Validate BED columns

        Note: This function forces standard column names!
        """
        num_cols = len(self._specs["columns"])
        cols = [l.strip() for l in line.split(self._sep)]
        # silently ignore extra cols
        cols = cols[:num_cols]
        # allow BED6, BED11, and BED12 (w/ refBase, but not standard BED12)
        # HARD CODED!
        self._num_col = len(cols)
        if self._num_col not in [6, 11, 12]:
            msg = "Invalid format! Only BED6 or bedRMod/EUF (11 or 12 columns)."
            raise SpecsError(msg)
        int_cols = [
            "start",
            "end",
            "score",
            "thick_start",
            "thick_end",
            "coverage",
            "frequency",
        ]
        if self._num_col == 6:
            int_cols = int_cols[:3]
        # for type casting
        self._int_types = [
            i
            for i, v in enumerate(
                itertools.islice(self._specs["columns"].keys(), self._num_col)
            )
            if v in int_cols
        ]

    def _munge_values(self, values: list[str]) -> dict:
        """Read data records into dictionary, cast types to those required by the model.

        :param values: Records for one line
        :type lines: list
        :returns: Records as a dict
        :rtype: dict
        """
        num_values = len(values)
        if num_values != self._num_col:
            raise ValueError("Column count doesn't match value count!")
        # first cast to float all numerical types, then type cast model (int or float)
        # NOTE: data loss may occur if e.g. coverage or frequency are wrongly assumed to be float
        cvalues = [
            float(v) if i in self._int_types else v for i, v in enumerate(values)
        ]
        data = {
            c: self._dtypes["Data"][c].__call__(cvalues[i])
            for i, c in enumerate(
                itertools.islice(self._specs["columns"].values(), self._num_col)
            )
        }
        data["dataset_id"] = self._dataset_id
        # AD HOC * fill remaining columns based on query order *
        # ignore columns that are not queried!
        if self._num_col < 11:
            data["coverage"] = 0
            data["frequency"] = 0
        data = {k: data[k] for k in self.QORDER}
        return data

    def _read_line(self, line: str) -> None:
        """Read a line, buffer data for insert."""
        values = [l.strip() for l in line.split(self._sep)]
        # error handling...
        validated_values = self._munge_values(values)
        self._records.append(validated_values)
