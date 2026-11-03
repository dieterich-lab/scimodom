"""Argument parsing and consistency.

No service is called: these tests only cover what Click does before a
command body runs, and that all commands follow the same conventions.
"""

import pytest
from flask import Flask

from scimodom.cli.annotation import annotation_cli
from scimodom.cli.assembly import assembly_cli
from scimodom.cli.charts import charts_cli
from scimodom.cli.dataset import dataset_cli
from scimodom.cli.project import project_cli
from scimodom.cli.selection import selection_cli

BLUEPRINTS = [
    assembly_cli,
    annotation_cli,
    selection_cli,
    project_cli,
    dataset_cli,
    charts_cli,
]

COMMANDS = [
    (blueprint.name, name, command)
    for blueprint in BLUEPRINTS
    for name, command in blueprint.cli.commands.items()
]
COMMAND_IDS = [f"{group} {name}" for group, name, _ in COMMANDS]
# commands that do not modify data, and do not ask for confirmation
READ_ONLY_COMMANDS = {"charts sunburst-update"}


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
    yield app.test_cli_runner()


def test_all_commands_are_covered():
    # fails if a CLI module (blueprint) is not listed above
    expected = {
        "assembly add",
        "annotation add",
        "selection add",
        "project create-template",
        "project add",
        "project add-user",
        "project delete",
        "dataset add",
        "dataset batch",
        "charts sunburst-update",
    }
    assert set(COMMAND_IDS) == expected


@pytest.mark.parametrize("group, name, command", COMMANDS, ids=COMMAND_IDS)
def test_help(test_runner, group, name, command):
    result = test_runner.invoke(args=[group, name, "--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


@pytest.mark.parametrize("group, name, command", COMMANDS, ids=COMMAND_IDS)
def test_commands_have_common_options(group, name, command):
    options = {opt for param in command.params for opt in param.opts}
    assert "--traceback" in options
    if f"{group} {name}" not in READ_ONLY_COMMANDS:
        # data changing commands must be usable non-interactively
        assert "--yes" in options


# usage errors exit with code 2 (Click), before any service is called


@pytest.mark.parametrize(
    "args",
    [
        ["assembly", "add"],  # missing ASSEMBLY_ID
        ["assembly", "add", "not-a-number"],
        ["annotation", "add", "1"],  # missing --source
        ["annotation", "add", "--source", "bogus", "1"],
        ["project", "add"],
        ["project", "delete"],
        ["project", "add-user", "only-one-argument"],
        ["dataset", "batch", "--annotation", "ensembl"],
    ],
)
def test_usage_errors(test_runner, args):
    result = test_runner.invoke(args=args)
    assert result.exit_code == 2
    assert "Usage:" in result.output


def test_dataset_batch_invalid_annotation(test_runner, tmp_path):
    result = test_runner.invoke(
        args=["dataset", "batch", "--annotation", "bogus", tmp_path.as_posix(), "UUID"]
    )
    assert result.exit_code == 2
    assert "Invalid value for '--annotation'" in result.output


def test_dataset_batch_input_directory_must_exist(test_runner, tmp_path):
    result = test_runner.invoke(
        args=[
            "dataset",
            "batch",
            "--annotation",
            "ensembl",
            (tmp_path / "missing").as_posix(),
            "UUID",
        ]
    )
    assert result.exit_code == 2


def _dataset_add_args(tmp_path, title="Title", annotation="ensembl"):
    filename = tmp_path / "file.bedrmod"
    filename.write_text("")
    return [
        "dataset",
        "add",
        "--yes",
        "--assembly-id",
        "1",
        "--annotation",
        annotation,
        "-m",
        "1",
        "-o",
        "1",
        "-t",
        "1",
        filename.as_posix(),
        "SMID",
        title,
    ]


def test_dataset_add_title_too_long(test_runner, tmp_path):
    result = test_runner.invoke(args=_dataset_add_args(tmp_path, title="x" * 256))
    assert result.exit_code == 2
    assert "Title cannot be longer than 255 characters" in result.output


def test_dataset_add_invalid_annotation(test_runner, tmp_path):
    result = test_runner.invoke(args=_dataset_add_args(tmp_path, annotation="bogus"))
    assert result.exit_code == 2
    assert "Invalid value for '--annotation'" in result.output


def test_dataset_add_file_must_exist(test_runner, tmp_path):
    args = _dataset_add_args(tmp_path)
    args[args.index((tmp_path / "file.bedrmod").as_posix())] = (
        tmp_path / "missing.bedrmod"
    ).as_posix()
    result = test_runner.invoke(args=args)
    assert result.exit_code == 2


def test_project_create_template_date_format(test_runner, tmp_path):
    csv = tmp_path / "datasets.csv"
    csv.write_text("file\n")
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
    assert "--published" in result.output
