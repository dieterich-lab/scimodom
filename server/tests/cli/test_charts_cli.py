from pathlib import Path

import pytest
from flask import Flask

from scimodom.cli.charts import charts_cli
from scimodom.services.file import FileService
from scimodom.services.sunburst import SunburstService


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_sunburst_service(Session, tmp_path):
    return SunburstService(
        session=Session(),
        file_service=_get_file_service(Session, tmp_path),
    )


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(charts_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path):
    mocker.patch(
        "scimodom.cli.charts.get_sunburst_service",
        return_value=_get_sunburst_service(Session, tmp_path),
    )


# tests


def test_sunburst_update(Session, tmp_path, mock_services, test_runner):
    result = test_runner.invoke(args=["charts", "sunburst-update"])
    assert result.exit_code == 0
    d = tmp_path / "t_data" / FileService.SUNBURST_CACHE_DEST
    for f in ["search.json", "browse.json"]:
        assert Path(d, f).exists() is True
