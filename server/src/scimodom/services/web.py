from pathlib import Path
from typing import BinaryIO

import requests


class WebService:
    @staticmethod
    def request_as_json(url: str) -> dict:
        """Send request, and return response to dictionary.

        :param url: URL
        :type url: str
        :returns: Response as json
        :rtype: dict
        """
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            request.raise_for_status()
        return request.json()

    @staticmethod
    def stream_request_to_file(url: str, stream: BinaryIO):
        """Stream request to file.

        :param url: URL
        :type url: str
        :param path: File path
        :type path: str or Path
        :param mode: Mode used to open the output file - default "wb"

        """
        with requests.get(url, stream=True) as request:
            if not request.ok:
                request.raise_for_status()
            for chunk in request.iter_content(chunk_size=1024 * 1024):
                stream.write(chunk)


def get_web_service():
    return WebService()
