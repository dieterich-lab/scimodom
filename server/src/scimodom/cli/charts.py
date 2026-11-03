"""Provide a CLI for background charts update."""

import click
from flask import Blueprint

from scimodom.cli.helpers import CliResponseException, register_cli_errors
from scimodom.services.file import SunburstUpdateAlreadyRunning
from scimodom.services.sunburst import get_sunburst_service

charts_cli = Blueprint("charts", __name__)


@charts_cli.cli.command(
    "sunburst-update",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option("--traceback", is_flag=True, help="Show traceback")
def sunburst_update(traceback: bool):
    """Update the cached data for the sunburst charts.

    This should be done after a dataset has been added.
    Usually this is triggered automatically and executed
    in the background.
    """
    try:
        click.secho("Updating sunburst charts data ...", fg="yellow")
        sunburst_service = get_sunburst_service()
        sunburst_service.do_background_update()
    except SunburstUpdateAlreadyRunning:
        click.secho("Nothing to do - already running.", fg="yellow")
        return
    except Exception as exc:
        raise CliResponseException(f"Failed to update sunburst charts. {exc}") from exc
    click.secho("   ... done.", fg="green")
