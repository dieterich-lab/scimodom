from typing import TextIO, Generator

from pydantic import ValidationError


class TextFileReaderError(Exception):
    """Exception for handling general text file reader errors."""

    pass


class TextFileReader:
    """Provide a text file reader."""

    def __init__(
        self,
        stream: TextIO,
        source: str = "input_stream",
    ):
        self._stream = stream
        self._source = source
        self._line_number = 0

    def read_lines(self) -> Generator[str, None, None]:
        """Read lines.

        :return: All lines in stream.
        :rtype: Generator
        """
        for line in self._stream:
            self._line_number += 1
            stripped_line = line.strip()
            yield stripped_line

    def report_error(self, message: str) -> None:
        """Report reading error.

        :param message: Error message.
        :type message: str
        :raises TextFileReaderError: If failed to read stream.
        """
        raise TextFileReaderError(
            f"{self._source}, line {self._line_number}: {message}"
        )

    def report_error_pydantic_error(self, error: ValidationError) -> None:
        """Report validation error.

        :param error: Pydantic validation error
        :type error: ValidationError
        """
        message = "; ".join(
            [f"{'/'.join(list(e['loc']))}: {e['msg']}" for e in error.errors()]  # type: ignore
        )
        self.report_error(message)
