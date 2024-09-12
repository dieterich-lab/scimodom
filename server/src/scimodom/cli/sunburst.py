import click

from scimodom.services.file import SunburstUpdateAlreadyRunning
from scimodom.services.sunburst import get_sunburst_service


def update_sunburst_chart():
    try:
        click.secho("Updating Sunburst chart data ...", fg="green")
        sunburst_service = get_sunburst_service()
        sunburst_service.do_background_update()
    except SunburstUpdateAlreadyRunning:
        click.secho("Nothing to do - already running,", fg="green")
    except Exception as exc:
        click.secho("    ... FAILED!", fg="red")
        click.secho(f"Failed to update sunburst charts: {exc}... Aborting!", fg="red")
        raise click.Abort()
    click.secho("    ... done.", fg="green")
