import logging
from typing import TextIO, Optional, Generator
import re

from pydantic import ValidationError

from scimodom.utils.bedtools_dto import ModificationRecord, Strand, NO_SUCH_DATASET_ID
from scimodom.utils.text_file_reader import TextFileReader, TextFileReaderError

logger = logging.getLogger(__name__)


class BedImportEmptyFile(Exception):
    pass


class BedImportTooManyErrors(Exception):
    pass


class BedImporter:
    BED_HEADER_REGEXP = re.compile(r"\A#([a-zA-Z_]+)=(.*)\Z")
    MAX_ERROR_RATE = 0.05

    def __init__(
        self, stream: TextIO, is_euf: bool = False, source: str = "input stream"
    ):
        self._headers = {}
        self._error_count = 0
        self._record_count = 0

        self._is_euf = is_euf
        self._source = source

        self._reader = TextFileReader(stream=stream, source=source)
        self._line_iterator = self._reader.read_lines()
        self._next_record = (
            self._get_next_record()
        )  # Bootstrap iterator to force parsing of header records

    def _get_next_record(self):
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

    def _get_record_from_line(self, line) -> ModificationRecord:
        try:
            try:
                fields = [x.strip() for x in line.split("\t")]
                if self._is_euf:
                    raw_record = self._get_raw_record_from_euf_line(fields)
                else:
                    raw_record = self._get_raw_record_from_bed6_line(fields)
                return ModificationRecord(**raw_record)
            except ValidationError as err:
                self._reader.report_error_pydantic_error(err)
            except ValueError as err:
                self._reader.report_error(str(err))
        except TextFileReaderError as err:
            self._error_count += 1
            logger.warning(str(err))

    def _get_raw_record_from_euf_line(self, fields):
        if len(fields) < 11:
            self._reader.report_error(f"Expected 11 fields, but got {len(fields)}")
        return {
            "chrom": fields[0],
            "start": fields[1],
            "end": fields[2],
            "name": fields[3],
            "score": fields[4],
            "strand": Strand(fields[5]),
            "coverage": fields[9],
            "frequency": fields[10],
            "dataset_id": NO_SUCH_DATASET_ID,
        }

    def _get_raw_record_from_bed6_line(self, fields):
        if len(fields) < 6:
            self._reader.report_error(f"Expected 6 fields, but got {len(fields)}")
        return {
            "chrom": fields[0],
            "start": fields[1],
            "end": fields[2],
            "name": fields[3],
            "score": fields[4],
            "strand": Strand(fields[5]),
            "coverage": 0,
            "frequency": 0,
            "dataset_id": NO_SUCH_DATASET_ID,
        }

    def get_header(self, name: str) -> Optional[str]:
        if name in self._headers:
            return self._headers[name]
        else:
            return None

    def parse(self) -> Generator[ModificationRecord, None, None]:
        record = self._next_record
        while record is not None:
            yield record
            record = self._get_next_record()

        if self._record_count == 0:
            msg = f"Did not find any records in '{self._source}'"
            logger.error(msg)
            raise BedImportEmptyFile(msg)
        if self._error_count > self._record_count * self.MAX_ERROR_RATE:
            msg = (
                f"Found too many errors ins '{self._source}' "
                f"(valid: {self._record_count}, errors: {self._error_count})"
            )
            logger.error(msg)
            raise BedImportTooManyErrors(msg)
