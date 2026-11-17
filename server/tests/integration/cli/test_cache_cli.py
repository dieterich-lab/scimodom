import json
from pathlib import Path

import pytest
from flask import Flask

from scimodom.cli.cache import cache_cli
from scimodom.services.file import FileService
from scimodom.services.modification import ModificationService
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


def _get_modification_service(Session, tmp_path):
    return ModificationService(
        session=Session(),
        annotation_service=None,
        file_service=_get_file_service(Session, tmp_path),
    )


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(cache_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path):
    mocker.patch(
        "scimodom.cli.cache.get_sunburst_service",
        return_value=_get_sunburst_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.cache.get_modification_service",
        return_value=_get_modification_service(Session, tmp_path),
    )


def _sunburst_files(tmp_path):
    d = tmp_path / "t_data" / FileService.INDEX_CACHE_DEST
    return [Path(d, f) for f in ["sunburst_search.json", "sunburst_browse.json"]]


def _aggregates_file(tmp_path):
    return Path(
        tmp_path, "t_data", FileService.INDEX_CACHE_DEST, "modification_aggregates.json"
    )


# tests


def test_update_sunburst(Session, tmp_path, mock_services, test_runner):
    result = test_runner.invoke(args=["cache", "update-sunburst"])
    assert result.exit_code == 0
    assert all(f.exists() for f in _sunburst_files(tmp_path))
    assert _aggregates_file(tmp_path).exists() is False


def test_update_aggregates(Session, tmp_path, mock_services, test_runner, dataset):
    result = test_runner.invoke(args=["cache", "update-aggregates"])
    assert result.exit_code == 0
    assert not any(f.exists() for f in _sunburst_files(tmp_path))
    with open(_aggregates_file(tmp_path)) as fh:
        content = json.load(fh)
    assert sum(stratum["records"] for stratum in content["strata"]) == 7
    assert sum(stratum["sites"] for stratum in content["strata"]) == 6


def test_update_all(Session, tmp_path, mock_services, test_runner, dataset):
    result = test_runner.invoke(args=["cache", "update"])
    assert result.exit_code == 0
    assert all(f.exists() for f in _sunburst_files(tmp_path))
    assert _aggregates_file(tmp_path).exists()


def test_update_all_continues_after_failure(
    mocker, Session, tmp_path, mock_services, test_runner
):
    mocker.patch(
        "scimodom.cli.cache._update_sunburst", side_effect=RuntimeError("Exception")
    )
    result = test_runner.invoke(args=["cache", "update"])
    assert result.exit_code == 1
    assert "Exception" in result.output
    # the other cache is still updated
    assert _aggregates_file(tmp_path).exists()


def test_update_aggregates_already_running(mocker, test_runner):
    from scimodom.services.file import CacheUpdateAlreadyRunning

    service = mocker.Mock()
    service.do_aggregates_update.side_effect = CacheUpdateAlreadyRunning
    mocker.patch("scimodom.cli.cache.get_modification_service", return_value=service)
    result = test_runner.invoke(args=["cache", "update-aggregates"])
    assert result.exit_code == 0
    assert "already running" in result.output
