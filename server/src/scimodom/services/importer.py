import re

from sqlalchemy import insert

import scimodom.utils.utils as utils
import scimodom.database.queries as queries
from scimodom.database.models import Data, Dataset

from sqlalchemy import select

import logging

logger = logging.getLogger(__name__)

# if needed
# from abc import ABC, abstractmethod
# BaseImporter(ABC):
#   @abstractmethod
#   def parse(self, data):
# then define given importer e.g. MyImporter(BaseImporter)


# define EUF specs

specsEUF = {
    "format": "bedRMod",
    "header": {"comment": "#", "delimiter": "="},
    "delimiter": "\t",
    "1.6": {
        "headers": {
            "fileformat": "file_format",
            "organism": "taxa_id",
            "modification_type": "modification_type",
            "assembly": "assembly_id",
            "annotation_source": "annotation_source",
            "annotation_version": "annotation_version",
            "sequencing_platform": "sequencing_platform",
            "basecalling": "basecalling",
            "bioinformatics_workflow": "bioinformatics_workflow",
            "experiment": "experiment",
            "external_source": "external_source",
        },
        "columns": {
            "chrom": "chrom",
            "chromStart": "start",
            "chromEnd": "end",
            "name": "name",
            "score": "score",
            "strand": "strand",
            "thickStart": "thick_start",
            "thickEnd": "thick_end",
            "itemRgb": "item_rgb",
            "coverage": "coverage",
            "frequency": "frequency",
            "refBase": "ref_base",
        },
    },
}


class SpecsError(Exception):
    pass


class EUFImporter:
    """
    Reads data from bedRMod file and writes to database tables.
    """

    class _Buffer:
        MAX_BUFFER = 1000

        def __init__(self, session, model):
            self._session = session
            self._model = model
            self._buffer = []

        def buffer_data(self, d):
            self._buffer.append(d)
            if len(self._buffer) >= self.MAX_BUFFER:
                self.flush()

        def flush(self):
            if not self._buffer:
                return
            self._session.execute(insert(self._model), self._buffer)
            self._buffer = []

    def __init__(
        self,
        session,
        filen,
        handle,
        smid,
        eufid,
        title,
        taxa_id,
        assembly_id,
        lifted,
    ):
        self._sep = specsEUF["delimiter"]
        self._htag = specsEUF["header"]["comment"]
        self._hsep = specsEUF["header"]["delimiter"]
        self._version = None
        self._specs = None

        self._session = session
        self._filen = filen
        self._handle = handle

        self._lino = None
        self._header = None
        self._buffers = dict()
        self._dtypes = dict()
        self._modifications_from_file = set()

        # presumably, SMID, title, taxa_id, assembly_id all come from the FE upload form
        # or from arguments to the API/maintenance -> TODO: data upload service
        # there we should check if SMID, taxa_id, and assembly_id are valid choices
        # here, we assume they are already checked
        self._eufid = eufid
        self._smid = smid
        self._title = title
        self._taxa_id = taxa_id
        self._assembly_id = assembly_id
        self._lifted = lifted

    def close(self):
        self._handle.close()
        for _buffer in self._buffers.values():
            _buffer.flush()
        self._session.commit()

    def parseEUF(self):
        self._lino = 1
        self._read_version()

        self._validate_attributes(Dataset, self._specs["headers"].values())
        self._validate_attributes(Data, self._specs["columns"].values())

        self._buffers["Dataset"] = EUFImporter._Buffer(
            session=self._session, model=Dataset
        )
        self._read_header()

        self._buffers["Data"] = EUFImporter._Buffer(session=self._session, model=Data)
        self._validate_columns()
        for line in self._handle:
            self._lino += 1
            self._read_line(line)

    def _read_version(self):
        try:
            line = next(self._handle)
        except StopIteration:
            raise EOFError(f" {self._filen}")
        version = ".".join(re.findall(r"\d+", line))
        try:
            self._version = f"{specsEUF['format']}v{version}"
            self._specs = specsEUF[version]
        except KeyError:
            raise SpecsError(f" Unknown version: {self._version}.")

    def _validate_attributes(self, model, specs):
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

    def _add_missing_header_fields(self, assembly):
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

    def _munge_header(self, lines):
        def _get_header(header):
            h = f"{self._htag}{header}{self._hsep}"
            s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
            if not s:
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
        return _get_header("assembly")

    def _read_header(self):
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

    def _validate_columns(self):
        num_cols = len(self._specs["columns"])
        line = next(self._handle).replace(self._htag, "")
        self._lino += 1
        cols = [l.strip() for l in line.split(self._sep)]
        extra_cols = cols[num_cols:]
        for col in extra_cols:
            msg = f"Extra column '{col}' from {self._filen} will be ignored."
            logger.warning(msg)
        cols = cols[:num_cols]
        if len(cols) != num_cols:
            msg = f"Column count doesn't match required count at row {self._lino} for {self._version}."
            raise SpecsError(msg)
        # Is it safe? How to overwrite if this happens (EUFID assignment, etc.)?
        for col_read, col_specs in zip(cols, self._specs["columns"].keys()):
            if not col_read.lower() == col_specs.lower():
                msg = (
                    f"Column name '{col_read}' from {self._filen} differs from the required {col_specs}. "
                    f"Data import will continue, assuming conformity to {self._version}. "
                    f"If you suspect misformatting, or data corruption, check {self._filen} and start again!"
                )
                logger.warning(msg)

    def _munge_values(self, values):
        num_values = len(values)
        num_cols = len(self._specs["columns"])
        if num_values != num_cols:
            raise ValueError(
                f"Column count doesn't match value count at row {self._lino}"
            )
        data = {
            c: self._dtypes["Data"][c].__call__(values[i])
            for i, c in enumerate(self._specs["columns"].values())
        }
        data["dataset_id"] = self._eufid
        return data

    def _read_line(self, line):
        values = [l.strip() for l in line.split(self._sep)]
        try:
            validated_values = self._munge_values(values)
            self._modifications_from_file.add(validated_values["name"])
            self._buffers["Data"].buffer_data(validated_values)
        except ValueError as error:
            msg = f"Warning: Failed to parse {self._filen} at row {self._lino}: {error} - skipping!"
            logger.warning(msg)

    def get_modifications_from_file(self):
        return self._modifications_from_file
