from pathlib import Path
from typing import BinaryIO

import requests


class WebService:
    """Utility class for stream and requests."""

    # (connect, read) in seconds
    # read: received bytes, not whole transfer, does not limit size of downloads
    CONNECT_TIMEOUT = 10
    READ_TIMEOUT = 60
    TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

    @staticmethod
    def request_as_json(url: str) -> dict:
        """Send request, and return response to dictionary.

        :param url: URL
        :raises requests.Timeout: If the server does not respond in time.
        :return: Response as json
        """
        request = requests.get(
            url,
            headers={"Content-Type": "application/json"},
            timeout=WebService.TIMEOUT,
        )
        if not request.ok:
            request.raise_for_status()
        return request.json()

    @staticmethod
    def stream_request_to_file(url: str, stream: BinaryIO):
        """Stream request to file.

        :param url: URL
        :param path: File path
        :param mode: Mode used to open the output file - default "wb"
        """
        with requests.get(url, stream=True, timeout=WebService.TIMEOUT) as request:
            if not request.ok:
                request.raise_for_status()
            for chunk in request.iter_content(chunk_size=1024 * 1024):
                stream.write(chunk)


def get_web_service():
    """Instantiate a WebService object.

    :return: Web service instance
    """
    return WebService()
