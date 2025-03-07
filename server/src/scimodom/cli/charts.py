import click
from flask import Blueprint

from scimodom.services.file import SunburstUpdateAlreadyRunning
from scimodom.services.sunburst import get_sunburst_service


charts_cli = Blueprint("charts", __name__)


@charts_cli.cli.command(
    "sunburst-update",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html.",
)
def sunburst_update():
    """Update the cached data for the sunburst charts.

    This should be done after a dataset has been added.
    Usually this is triggered automatically and executed
    in the background.
    """
    try:
        click.secho("Updating sunburst charts data ...", fg="green")
        sunburst_service = get_sunburst_service()
        sunburst_service.do_background_update()
    except SunburstUpdateAlreadyRunning:
        click.secho("Nothing to do - already running.", fg="yellow")
        return
    except Exception as exc:
        click.secho(f"Failed to update sunburst charts. {exc}", fg="red")
        raise click.Abort()
    click.secho("   ... done.", fg="green")
