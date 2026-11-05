import click
import click.testing
import pytest

from scimodom.cli.helpers import (
    CliResponseException,
    confirm,
    register_cli_errors,
)


@pytest.fixture
def runner():
    return click.testing.CliRunner()


@pytest.fixture
def command():
    @click.command()
    @register_cli_errors
    @click.option("--yes", is_flag=True)
    @click.option("--fail", is_flag=True)
    @click.option("--traceback", is_flag=True)
    def cmd(yes, fail, traceback):
        confirm("delete everything?", skip=yes)
        if fail:
            raise CliResponseException("Exception")
        click.echo("done")

    return cmd


def test_confirm(runner, command, mocker):
    mocker.patch("scimodom.cli.helpers.common._is_interactive", return_value=True)
    result = runner.invoke(command, input="y\n")
    assert result.exit_code == 0
    assert "done" in result.stdout


def test_confirm_skip(runner, command):
    result = runner.invoke(command, ["--yes"])
    assert result.exit_code == 0
    assert "done" in result.stdout


def test_confirm_non_interactive_is_usage_error(runner, command):
    result = runner.invoke(command)
    assert result.exit_code == 2


def test_traceback_reraises(runner, command):
    result = runner.invoke(command, ["--yes", "--fail", "--traceback"])
    # w/ traceback: CliRunner puts unhandled exceptions in result.exception
    # w/o traceback: exception shows up as SystemExit with formatted stderr
    assert result.stderr == ""
    assert isinstance(result.exception, CliResponseException)
