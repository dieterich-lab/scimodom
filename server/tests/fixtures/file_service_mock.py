from os import close
from tempfile import mkstemp

import pytest

from scimodom.services.file import FileService


class FileServiceMock(FileService):
    def __init__(self, tmpdir):  # noqa
        self._tmpdir = tmpdir

    def create_temp_file(self, suffix="") -> str:
        fp, path = mkstemp(dir=self._tmpdir, suffix=suffix)
        close(fp)
        return path

    def get_temp_path(self) -> str:
        return self._tmpdir


@pytest.fixture
def file_service(tmpdir):
    yield FileServiceMock(tmpdir)
