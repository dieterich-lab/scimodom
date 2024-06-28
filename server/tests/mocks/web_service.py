from pathlib import Path
from typing import BinaryIO


class MockHTTPError(Exception):
    pass


class MockWebService:
    def __init__(
        self,
        url_to_result: dict[str, dict] | None = None,
        url_to_data: list[str] | None = None,
    ):
        self._url_to_result = {} if url_to_result is None else url_to_result
        self._url_to_data = {} if url_to_data is None else url_to_data

    def request_as_json(self, url: str) -> dict:
        if url not in self._url_to_result:
            raise MockHTTPError("Mock: Not found!")
        return self._url_to_result[url]

    def stream_request_to_file(self, url: str, stream: BinaryIO):
        if url not in self._url_to_data:
            raise MockHTTPError("Mock: No such download!")
        stream.write(self._url_to_data[url])
