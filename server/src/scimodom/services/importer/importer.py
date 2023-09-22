import re

from sqlalchemy import insert

import scimodom.utils.utils as utils
import scimodom.database.queries as queries
from scimodom.database.models import Data, Dataset

import logging

logger = logging.getLogger(__name__)

# if needed
# from abc import ABC, abstractmethod
# BaseImporter(ABC):
#   @abstractmethod
#   def parse(self, data):
# then define given importer e.g. MyImporter(BaseImporter)


specsEUF = {
    "format": "bedRMod",  # unused
    "header": {"comment": "#", "delimiter": "="},
    "delimiter": "\t",  # no regex, i.e. we want only one tab between fields, and no extra tab at the end
    "1.6": {
        # specs: mapped columns - silently replace with mapped columns
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

    def __init__(self, session, filen, handle):
        self._session = session
        self._filen = filen
        self._handle = handle

        self.MAX_BUFFER = 1000
        self.EUFID_LENGTH = 12

        self._fmt = specsEUF["format"]
        self._sep = specsEUF["delimiter"]
        self._htag = specsEUF["header"]["comment"]
        self._hsep = specsEUF["header"]["delimiter"]
        self._version = None
        self._specs = None

        self._lino = None
        self._buffer = []
        self._dtypes = dict()

    # TODO: we also need a method to assign assocaition table from input
    # so we need to have selection.id (or query from modification, technology, organism)
    # these fields are presumably filled at upload on the FE form (after being available
    # via SMID/projetc creation).
    # if via API/maintenance, we need to provide these as args, to get selection.id
    # and make sure they are valid choices.

    def create_dataset(
        self,
        smid=None,  # str
        title=None,  # str
        taxa_id=None,  # int
        assembly_id=None,  # int
    ):
        # TODO: type hints/define instead
        if None in {smid, title, taxa_id, assembly_id}:
            raise TypeError("Calling 'create_dataset' require defined arguments!")

        # presumably, SMID, title, taxa_id, assembly_id all come from the FE upload form
        # or from arguments to the API/maintenance -> TODO: data upload service
        # there we should check if SMID, taxa_id, and assembly_id are valid choices
        # here, we assume they are already checked
        self._smid = smid
        self._title = title
        self._taxa_id = taxa_id
        self._assembly_id = assembly_id
        self._lifted = False

        query = queries.assembly("version", filters={"id": self._assembly_id})
        assembly_version = self._session.execute(query).scalar()

        query = queries.get_assembly_version()
        db_assembly_version = self._session.execute(query).scalar()

        if not assembly_version == db_assembly_version:
            self._lifted = True
            print("Some message...")

        query = queries.dataset("id")
        eufids = self._session.execute(query).scalars().all()
        self._eufid = utils.gen_short_uuid(self.EUFID_LENGTH, eufids)

    def _buffer_data(self, d):
        self._buffer.append(d)
        if len(self._buffer) >= self.MAX_BUFFER:
            self._flush()

    def _flush(self):
        if not self._buffer:
            return
        self._session.execute(insert(Data), self._buffer)
        self._buffer = []

    def _close(self):
        self._handle.close()
        self._flush()
        self._session.commit()

    def parseEUF(self):
        self._lino = 1
        self._read_version()

        self._validate_attributes(Dataset, self._specs["headers"].values())
        self._validate_attributes(Data, self._specs["columns"].values())

        self._read_header()

        self._validate_columns()

        # maybe we don;'t need to lino?
        # after header, we could use readlines, instead of line by line?

        # TODO
        # header type formatting, e.g. taxid
        # read actual data - type formattign again
        # make sure we have 12 fields all the time
        # store in column/field header: value - check
        # buffering, table update

        # TODO: how to assembly management?

        for line in self._handle:
            self._lino += 1
            self._read_line(line)
        self._close()

    def _read_version(self):
        try:
            line = next(self._handle)
        except StopIteration:
            raise EOFError(f" {self._filen}")
        self._version = ".".join(re.findall(r"\d+", line))
        try:
            self._specs = specsEUF[self._version]
        except KeyError:
            raise SpecsError(f" Unknown version: {self._fmt}v{self._version}.")
        # try:
        #   idx = line.lower().rindex(self._fmt.lower()) + len(self._fmt)
        # except ValueError:
        #   raise SpecsError(f" Supported file format: {self._fmt}.")
        # self._version = line[idx:].strip()

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
                logger.error(msg)
                raise Exception(msg)
            idx = mapped_columns.index(c)
            _dtypes[c] = mapped_types[idx]
        self._dtypes[model.__name__] = _dtypes

    # def _munge_header(self, lines, header):
    # h = f"{self._htag}{header}{self._hsep}"
    # s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
    # if s != []:
    ## (lines.index(s[0]), s[0]) if we need the index, do not replace/strip
    # return s[0]
    # return -1

    # def _munge_header(self, lines, headers):
    # header_dict = dict()
    # for header in headers:
    # h = f"{self._htag}{header}{self._hsep}"
    # s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
    # if not s:
    # raise SpecsError(f" Missing or misformatted header: {h}.")

    ## (lines.index(s[0]), s[0]) if we need the index, do not replace/strip
    # return s[0]
    # return -1

    def _munge_header(self, lines):
        header_dict = self._parse_header_from_file(lines)

    def _parse_header_from_file(self, lines):
        def _get_header(header, mapped_header):
            h = f"{self._htag}{header}{self._hsep}"
            s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
            if not s:
                raise SpecsError(f" Missing or misformatted header: {h}.")
            return self._dtypes["Dataset"][mapped_header].__call__(s[0])

        return {
            mapped_header: _get_header(header, mapped_header)
            for (header, mapped_header) in self._specs["headers"].items()
        }

    def _read_header(self):
        # or do reverse search, line by line ...?
        lines = []
        while self._lino < len(self._specs["headers"]):
            lines.append(next(self._handle))
            self._lino += 1

        header_dict = self._munge_header(lines)

        # TODO HERE:
        # 1 - mapped_headers and not headers must be assigned to dict
        # project_id (SMID), title
        # - assign EUFID (now auto int, but should be str)
        # 2 - neeed to assign file format
        # 3 - taxa_id and assembly_id must match ncbi_taxa.id and assembly.id (check taxa, but assmbly?)
        # 4 - lifted, annotation_source and annotation_version?
        # external_source may or may not match that of SMID, but we don't bother checking now

        # to delete
        # for header in headers[1:]:
        # value = self._munge_header(lines, header)
        # if value == -1:
        # raise SpecsError(
        # f" Missing or misformatted header: {self._htag}{header}{self._hsep}."
        # )
        # self._headers[header] = value

    # assign header

    # taxa_id and assembly_id must match ncbi_taxa.id and assembly.id
    # i.e. not from header, but from input (pass to class from FE or via API/script)
    # but we can still validate at least taxa, for assembly this is more tricky...

    # lifted?

    # annotation_source and annotation_version?

    # external_source may or maynot match that of SMID, but we don't bother checking now

    # TODO:
    # - check types
    # - assign EUFID (now auto int, but should be str) - keep it for later
    # - commit

    def _validate_columns(self):
        num_cols = len(self._specs["columns"])
        line = next(self._handle).replace(self._htag, "")
        self._lino += 1
        cols = [l.strip() for l in line.split(self._sep)]
        extra_cols = cols[num_cols:]
        for col in extra_cols:
            msg = f"Extra column '{col}' from {self._filen} will be ignored."
            logger.warning(msg)
            print(msg)
        cols = cols[:num_cols]
        # Is it safe? How to overwrite if this happens (EUFID assignment, etc.)?
        for col_read, col_specs in zip(cols, self._specs["columns"].keys()):
            if not col_read.lower() == col_specs.lower():
                msg = (
                    f"Column name '{col_read}' from {self._filen} differs from the required {col_specs}."
                    f"Data import will continue, assuming conformity to {self._fmt}v{self._version}."
                    f"If you suspect misformatting, or data corruption, check {self._filen} and start again!"
                )
                logger.warning(msg)
                print(msg)

    def _validate_values(self, values):
        num_values = len(values)
        num_cols = len(self._specs["columns"])
        if num_values != num_cols:
            raise ValueError(
                f"Column count doesn't match value count at row {self._lino}"
            )
        return {
            c: self._dtypes[c].__call__(values[i])
            for i, c in enumerate(self._specs["columns"].values())
        }

    def _read_line(self, line):
        values = [l.strip() for l in line.split(self._sep)]
        try:
            validated_values = self._validate_values(values)
            self._buffer_data(validated_values)
        except ValueError as error:
            msg = f"Warning: Failed to parse {self._filen} at row {self._lino}: {error} - skipping!"
            logger.warning(msg)
            print(msg)
