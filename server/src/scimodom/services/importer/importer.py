from abc import ABC, abstractmethod

import re

import logging

logger = logging.getLogger(__name__)

# class AbstractClass(ABC):

# @abstractmethod
# def abstractMethod(self):
# return

# class ConcreteClass(AbstractClass):

# def __init__(self):
# self.me = "me"

## Will get a TypeError without the following two lines:
##   def abstractMethod(self):
##       return 0

# c = ConcreteClass()
# c.abstractMethod()


specsEUF = {
    "format": "bedRMod",  # unused
    "header": {"comment": "#", "delimiter": "="},
    "delimiter": "\t",  # no regex, i.e. we want only one tab between fields, and no extra tab at the end
    "1.6": {
        "headers": [
            "fileformat",
            "organism",
            "modification_type",
            "assembly",
            "annotation_source",
            "annotation_version",
            "sequencing_platform",
            "basecalling",
            "bioinformatics_workflow",
            "experiment",
            "external_source",
        ],
        "columns": [  # force
            "chrom",
            "chromStart",
            "chromEnd",
            "name",
            "score",
            "strand",
            "thickStart",
            "thickEnd",
            "itemRgb",
            "coverage",
            "frequency",
            "refBase",
        ],
    },
}


class EmptyFileError(Exception):
    pass


class SpecsError(Exception):
    pass


class BaseImporter:
    """
    Abstract base class for importers.
    Reads data from file and writes to database tables.
    """

    def __init__(self, filen, handle):
        self._filen = filen
        self._handle = handle

        self._fmt = specsEUF["format"]
        self._sep = specsEUF["delimiter"]
        self._htag = specsEUF["header"]["comment"]
        self._hsep = specsEUF["header"]["delimiter"]
        self._version = None
        self._specs = None

        self._lino = None

        self._headers = dict()

    @abstractmethod
    def parseEUF(self, data):
        """
        Parse and validate rows.
        Returns a dict mapping the column names to the values (type-converted), and
        the corresponding SqlAlchemy model. Raises ValueError.
        """
        return

    def readEUF(self):
        self._lino = 1
        self._read_version()
        self._read_header()
        self._validate_cols()

        # maybe we don;'t need to lino?
        # after header, we could use readlines, instead of line by line?

        # TODO
        # header type formatting, e.g. taxid
        # read actual data - type formattign again
        # make sure we have 12 fields all the time
        # store in column/field header: value - check
        # buffering, table update

        # TODO: how to assembly management?

        # for line in self._handle:
        # self._lino += 1
        # self._process_line(line)
        # if self._line_number % 10000 == 0:
        # print(f"   ... at line {self._line_number} ...")
        # self._finish()

    def _read_version(self):
        try:
            line = next(self._handle)
        except StopIteration:
            raise EmptyFileError(f" {self._filen}")
        self._version = ".".join(re.findall(r"\d+", line))
        try:
            self._specs = specsEUF[self._version]
        except KeyError:
            raise SpecsError(f" Unknown version: {self._fmt}v{self._version}.")

        # try:
        # idx = line.lower().rindex(self._fmt.lower()) + len(self._fmt)
        # except ValueError:
        # raise SpecsError(f" Supported file format: {self._fmt}.")
        # self._version = line[idx:].strip()

        print(f"FORMAT = {self._version}")

    def _munge_header(self, lines, header):
        h = f"{self._htag}{header}{self._hsep}"
        s = [l.replace(h, "").strip() for l in lines if re.search(h, l)]
        if s != []:
            return s[
                0
            ]  # (lines.index(s[0]), s[0]) if we need the index, do not replace/strip
        return -1

    def _read_header(self):
        headers = self._specs["headers"]
        num_headers = len(headers) - 1
        # or do reverse search, line by line ...?
        lines = []
        while self._lino <= num_headers:
            lines.append(next(self._handle))
            self._lino += 1
        for header in headers[1:]:
            value = self._munge_header(lines, header)
            if value == -1:
                raise SpecsError(
                    f" Missing or misformatted header: {self._htag}{header}{self._hsep}."
                )
            self._headers[header] = value

        for k, v in self._headers.items():
            print(f"PARSED {k} = {v}")

    def _validate_cols(self):
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
        # is it safe? but how many times these names will be misspelled, etc.?
        for col_read, col_specs in zip(cols, self._specs["columns"]):
            if not col_read.lower() == col_specs.lower():
                msg = (
                    f"Column name '{col_read}' from {self._filen} differs from the required {col_specs}."
                    f"Data import will continue, assuming conformity to {self._fmt}v{self._version}."
                    f"If you suspect misformatting, or data corruption, check {self._filen} and start again."
                )
                logger.warning(msg)
                print(msg)
