import pytest
from flask import Flask

from scimodom.cli.dataset import dataset_cli
from scimodom.cli.project import project_cli


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(project_cli)
    app.register_blueprint(dataset_cli)
    yield app.test_cli_runner()


def test_dataset_add_title_too_long(test_runner, tmp_path):
    filename = tmp_path / "file.bedrmod"
    filename.write_text("")
    args = [
        "dataset",
        "add",
        "--yes",
        "--assembly-id",
        "1",
        "--rna-type",
        "WTS",
        "-m",
        "1",
        "-o",
        "1",
        "-t",
        "1",
        "SMID",
        "x" * 256,
        filename.as_posix(),
    ]
    result = test_runner.invoke(args=args)
    assert result.exit_code == 2
    assert "Title cannot be longer than 255 characters" in result.output


def test_project_create_template_date_format(test_runner, tmp_path):
    csv = tmp_path / "datasets.csv"
    csv.write_text("")
    result = test_runner.invoke(
        args=[
            "project",
            "create-template",
            "--yes",
            "--title",
            "T",
            "--summary",
            "S",
            "--surname",
            "A",
            "--forename",
            "B",
            "--institution",
            "I",
            "--email",
            "a@b.de",
            "--published",
            "02.11.2026",
            csv.as_posix(),
        ]
    )
    assert result.exit_code == 2
    assert (
        "Invalid value for '--published': '02.11.2026' does not match the format '%Y-%m-%d'"
        in result.output
    )
