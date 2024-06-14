import logging
from typing import TextIO, Optional, Generator
import re
from abc import ABC, abstractmethod

from pydantic import ValidationError

from scimodom.utils.bedtools_dto import (
    EufRecord,
    Strand,
    Bed6Record,
)
from scimodom.utils.text_file_reader import TextFileReader, TextFileReaderError

logger = logging.getLogger(__name__)


class BedImportEmptyFile(Exception):
    pass


class BedImportTooManyErrors(Exception):
    pass


class AbstractBedImporter(ABC):
    BED_HEADER_REGEXP = re.compile(r"\A#([a-zA-Z_]+)=(.*)\Z")

    def __init__(
        self,
        stream: TextIO,
        source: str = "input stream",
        max_error_rate: Optional[float] = 0.05,
    ):
        self._headers = {}
        self._error_count = 0
        self._record_count = 0

        self._source = source
        self._max_error_rate = max_error_rate

        self._reader = TextFileReader(stream=stream, source=source)
        self._line_iterator = self._reader.read_lines()
        self._next_record = (
            self._get_next_raw_record()
        )  # Bootstrap iterator to force parsing of header records

    def _get_next_raw_record(self):
        try:
            while True:
                line = self._line_iterator.__next__()
                if line.startswith("#"):
                    self._handle_comment(line)
                    continue
                if line == "":
                    continue
                record = self._get_record_from_line(line)
                if record is not None:
                    self._record_count += 1
                    return record
        except StopIteration:
            return None

    def _handle_comment(self, line):
        if self._record_count == 0:  # We are parsing the header
            match = self.BED_HEADER_REGEXP.match(line)
            if match is not None:
                self._headers[match.group(1)] = match.group(2)

    def _get_record_from_line(self, line):
        try:
            try:
                fields = [x.strip() for x in line.split("\t")]
                raw_record = self._get_raw_record_from_line(fields)
                return raw_record
            except ValidationError as err:
                self._reader.report_error_pydantic_error(err)
            except ValueError as err:
                self._reader.report_error(str(err))
        except TextFileReaderError as err:
            self._error_count += 1
            logger.warning(str(err))

    def report_error(self, message: str):
        try:
            self._reader.report_error(message)
        except TextFileReaderError as err:
            self._error_count += 1
            logger.warning(str(err))

    @abstractmethod
    def _get_raw_record_from_line(self, fields):
        pass

    def get_header(self, name: str) -> Optional[str]:
        if name in self._headers:
            return self._headers[name]
        else:
            return None

    def _parse_raw_records(self):
        record = self._next_record
        while record is not None:
            yield record
            record = self._get_next_raw_record()

        if self._record_count == 0:
            msg = f"Did not find any records in '{self._source}'"
            logger.error(msg)
            raise BedImportEmptyFile(msg)
        if (
            self._max_error_rate is not None
            and self._error_count > self._record_count * self._max_error_rate
        ):
            msg = (
                f"Found too many errors ins '{self._source}' "
                f"(valid: {self._record_count}, errors: {self._error_count})"
            )
            logger.error(msg)
            raise BedImportTooManyErrors(msg)

    @abstractmethod
    def parse(self):
        pass


class Bed6Importer(AbstractBedImporter):
    def _get_raw_record_from_line(self, fields):
        if len(fields) < 6:
            self._reader.report_error(f"Expected 6 fields, but got {len(fields)}")
        return {
            "chrom": fields[0],
            "start": fields[1],
            "end": fields[2],
            "name": fields[3],
            "score": fields[4],
            "strand": Strand(fields[5]),
        }

    def parse(self) -> Generator[Bed6Record, None, None]:
        for x in self._parse_raw_records():
            yield Bed6Record(**x)


class EufImporter(AbstractBedImporter):
    def _get_raw_record_from_line(self, fields):
        if len(fields) < 11:
            self._reader.report_error(f"Expected 11 fields, but got {len(fields)}")
        return {
            "chrom": fields[0],
            "start": fields[1],
            "end": fields[2],
            "name": fields[3],
            "score": fields[4],
            "strand": Strand(fields[5]),
            "thick_start": fields[6],
            "thick_end": fields[7],
            "item_rgb": fields[8],
            "coverage": fields[9],
            "frequency": fields[10],
        }

    def parse(self) -> Generator[EufRecord, None, None]:
        for x in self._parse_raw_records():
            yield EufRecord(**x)
