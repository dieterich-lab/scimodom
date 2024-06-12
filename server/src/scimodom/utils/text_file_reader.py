from typing import TextIO, Generator

from pydantic import ValidationError


class TextFileReaderError(Exception):
    pass


class TextFileReader:
    def __init__(
        self,
        stream: TextIO,
        source: str = "input_stream",
    ):
        self._stream = stream
        self._source = source
        self._line_number = 0

    def read_lines(self) -> Generator[str, None, None]:
        for line in self._stream:
            self._line_number += 1
            stripped_line = line.strip()
            yield stripped_line

    def report_error(self, message: str):
        raise TextFileReaderError(
            f"{self._source}, line {self._line_number}: {message}"
        )

    def report_error_pydantic_error(self, error: ValidationError):
        message = "; ".join(
            [f"{'/'.join(list(e['loc']))}: {e['msg']}" for e in error.errors()]
        )
        self.report_error(message)
