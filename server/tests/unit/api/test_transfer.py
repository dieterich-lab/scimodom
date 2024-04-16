from typing import Generator

import pytest
from flask import Flask

from scimodom.api.transfer import transfer_api
from scimodom.services.exporter import Exporter, NoSuchDataset


class ExporterMock(Exporter):
    def __init__(self):  # noqa
        pass

    def get_dataset_file_name(self, dataset_id: str) -> str:
        if dataset_id == "d1":
            return "foo"
        else:
            raise NoSuchDataset(f"No {dataset_id}")

    def generate_dataset(self, dataset_id: str) -> Generator[bytes, None, None]:
        if dataset_id == "d1":
            yield b"Line 1\n"
            yield b"Line 2\n"
        else:
            raise NoSuchDataset(f"No {dataset_id}")


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(transfer_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def exporter(mocker):
    mocker.patch("scimodom.api.transfer.get_exporter", return_value=ExporterMock())


def test_exporter_simple(test_client, exporter):
    result = test_client.get("/dataset/d1")
    assert result.status == "200 OK"
    assert result.data == b"Line 1\nLine 2\n"
    assert result.headers.get("Content-Disposition") == 'attachment; filename="foo"'
    assert result.headers.get("Content-Type") == "text/csv; charset=utf-8"


def test_exporter_bad_dataset(test_client, exporter):
    result = test_client.get("/dataset/d2")
    assert result.status == "404 NOT FOUND"
