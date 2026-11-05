import pytest
from flask import Flask

from scimodom.cli.setup import setup_cli
from scimodom.services.setup import SetupService

NAMES = ["rna_type.csv", "taxonomy.csv"]


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(setup_cli)
    yield app.test_cli_runner()


@pytest.fixture
def service(mocker):
    service = mocker.create_autospec(SetupService, instance=True)
    service.get_valid_import_file_names.return_value = NAMES
    service.is_valid_import_file.side_effect = lambda name: name in NAMES
    service.get_upsert_message.side_effect = lambda name: f"Updating {name}..."
    mocker.patch("scimodom.cli.setup.get_setup_service", return_value=service)
    return service


def test_upsert_all(test_runner, service):
    result = test_runner.invoke(args=["setup", "upsert", "--yes"])
    assert result.exit_code == 0
    service.upsert_all.assert_called_once


def test_upsert_selected(test_runner, service):
    result = test_runner.invoke(args=["setup", "upsert", "--yes", "taxonomy.csv"])
    assert result.exit_code == 0
    service.upsert_one.assert_called_once_with("taxonomy.csv")


def test_upsert_unknown_file_does_nothing(test_runner, service):
    result = test_runner.invoke(args=["setup", "upsert", "--yes", "nope.csv"])
    assert result.exit_code == 1
    assert (
        "Error: Unknown import file(s): nope.csv. Valid names are: rna_type.csv, taxonomy.csv."
        in result.stderr
    )
    service.upsert_one.assert_not_called()


def test_upsert_fails(test_runner, service):
    service.upsert_all.side_effect = ValueError("bad table")
    result = test_runner.invoke(args=["setup", "upsert", "--yes"])
    assert result.exit_code == 1
    assert "Failed to update database" in result.stderr
