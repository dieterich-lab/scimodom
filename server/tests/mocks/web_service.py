from pathlib import Path


class MockHTTPError(Exception):
    pass


class MockWebService:
    def __init__(
        self,
        url_to_result: dict[str, dict] | None = None,
        download_urls: list[str] | None = None,
    ):
        self._url_to_result = {} if url_to_result is None else url_to_result
        self._download_urls = [] if download_urls is None else download_urls

    def request_as_json(self, url: str) -> dict:
        if url not in self._url_to_result:
            raise MockHTTPError("Mock: Not found!")
        return self._url_to_result[url]

    def stream_request_to_file(self, url: str, path: str | Path, mode: str = "wb"):
        if url not in self._download_urls:
            raise MockHTTPError("Mock: No such download!")
