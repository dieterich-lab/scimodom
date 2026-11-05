import logging
import logging.config
import os
import pwd

import click
import click.testing
import pytest

from scimodom.cli.helpers import (
    CliResponseException,
    audited,
    confirm,
    register_cli_errors,
)
from scimodom.cli.helpers.audit import AUDIT_LOGGER_NAME


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines = []

    def emit(self, record):
        self.lines.append(record.getMessage())


@pytest.fixture
def records():
    handler = _Capture()
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield handler.lines
    logger.removeHandler(handler)
    logger.setLevel(level)


@pytest.fixture
def command():
    @click.command()
    @register_cli_errors
    @audited("audit")
    @click.option("--yes", is_flag=True)
    @click.option("--traceback", is_flag=True)
    @click.option("--mode", default="ok")
    @click.argument("name")
    def cmd(yes, traceback, mode, name):
        confirm("proceed?", skip=yes)
        if mode == "expected":
            raise CliResponseException("expected")
        if mode == "unexpected":
            raise RuntimeError("unexpected")
        click.echo("done")

    return cmd


@pytest.fixture
def runner():
    return click.testing.CliRunner()


def _user():
    return pwd.getpwuid(os.getuid()).pw_name


def test_success(runner, command, records):
    result = runner.invoke(command, ["--yes", "abc"])
    assert result.exit_code == 0
    assert len(records) == 2
    started, finished = records
    assert started.startswith("event=audit state=started")
    assert f"user={_user()} uid={os.getuid()}" in started
    assert 'command="cmd"' in started and '"name": "abc"' in started
    assert finished.startswith("event=audit state=finished outcome=success")


def test_expected_failure(runner, command, records):
    result = runner.invoke(command, ["--yes", "--mode", "expected", "abc"])
    assert result.exit_code == 1
    assert "Error: expected" in result.stderr
    assert "outcome=failed" in records[1]
    assert 'error="CliResponseException: expected"' in records[1]


def test_unexpected_failure(runner, command, records):
    result = runner.invoke(command, ["--yes", "--mode", "unexpected", "abc"])
    assert isinstance(result.exception, RuntimeError)
    assert result.exit_code == 1
    assert result.stderr == ""
    assert "outcome=failed" in records[1]
    assert "RuntimeError: unexpected" in records[1]


def test_aborted(runner, command, records, mocker):
    mocker.patch("scimodom.cli.helpers.common._is_interactive", return_value=True)
    result = runner.invoke(command, ["abc"], input="n\n")
    assert result.exit_code == 1
    assert "done" not in result.stdout
    assert "state=started" in records[0]
    assert "outcome=aborted" in records[1]


def test_non_interactive_without_yes_failure(runner, command, records):
    result = runner.invoke(command, ["abc"])
    assert result.exit_code == 2
    assert "outcome=failed" in records[1]
    assert (
        "UsageError: Cannot prompt for confirmation in non-interactive mode."
        in records[1]
    )


def test_usage_error_not_audited(runner, command, records):
    result = runner.invoke(command, [])
    assert result.exit_code == 2
    assert records == []


def test_keyboard_interrupt(records):
    @click.command()
    @audited("thing.x")
    def cmd():
        raise KeyboardInterrupt

    runner = click.testing.CliRunner()
    runner.invoke(cmd)
    assert "outcome=interrupted" in records[1]


def test_unknown_uid(runner, command, records, mocker):
    mocker.patch("scimodom.cli.helpers.audit.pwd.getpwuid", side_effect=KeyError(1))
    runner.invoke(command, ["--yes", "abc"])
    assert f"user=uid:{os.getuid()}" in records[0]


def test_audit_file_is_reopened_after_rotation(tmp_path):
    # a process that runs for a long time keeps writing to the live file
    from scimodom.cli.helpers.audit import AuditFileHandler

    path = tmp_path / "audit.log"
    handler = AuditFileHandler(path, encoding="utf-8", delay=True)
    logger = logging.getLogger("test.rotation")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        assert not path.exists()  # opened on the first record
        logger.info("one")
        path.rename(tmp_path / "audit.log.1")  # logrotate
        logger.info("two")
        assert path.read_text().strip() == "two"
        assert (tmp_path / "audit.log.1").read_text().strip() == "one"
    finally:
        logger.removeHandler(handler)
        handler.close()


def test_audit_file_failure_is_not_fatal(tmp_path, capsys):
    from scimodom.cli.helpers.audit import AuditFileHandler

    path = tmp_path / "missing" / "audit.log"
    handler = AuditFileHandler(path, encoding="utf-8", delay=True)
    logger = logging.getLogger("test.failure")
    logger.propagate = False
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    try:
        logger.info("one")  # does not raise
        assert f"failed to log audit record to '{path}'" in capsys.readouterr().err
        path.parent.mkdir()
        logger.info("two")  # the next record retries
        assert path.read_text().strip() == "two"
        assert capsys.readouterr().err == ""
    finally:
        logger.removeHandler(handler)
        handler.close()
