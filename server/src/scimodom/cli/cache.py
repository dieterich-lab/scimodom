"""Provide a CLI for background cache updates."""

from collections.abc import Callable

import click
from flask import Blueprint

from scimodom.cli.helpers import CliResponseException, register_cli_errors
from scimodom.services.file import CacheUpdateAlreadyRunning
from scimodom.services.modification import get_modification_service
from scimodom.services.sunburst import get_sunburst_service

cache_cli = Blueprint("cache", __name__)

EPILOG = "Consult https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management"


@cache_cli.cli.command("update-sunburst", epilog=EPILOG)
@register_cli_errors
@click.option("--traceback", is_flag=True, help="Show traceback")
def update_sunburst(traceback: bool):
    """Update the cached data for the sunburst charts.

    This should be done after a dataset has been added or removed.
    Usually this is triggered automatically and executed
    in the background.
    """
    if not _run_update("sunburst charts data", _update_sunburst):
        raise CliResponseException("Failed to update sunburst charts.")


@cache_cli.cli.command("update-aggregates", epilog=EPILOG)
@register_cli_errors
@click.option("--traceback", is_flag=True, help="Show traceback")
def update_aggregates(traceback: bool):
    """Update the cached aggregates (counts of records, sites).

    This should be done after a dataset has been added or removed.
    Usually this is triggered automatically and executed
    in the background.
    """
    if not _run_update("aggregates", _update_aggregates):
        raise CliResponseException("Failed to update aggregates.")


@cache_cli.cli.command("update", epilog=EPILOG)
@register_cli_errors
@click.option("--traceback", is_flag=True, help="Show traceback")
def update(traceback: bool):
    """Update all cached data (sunburst charts, aggregates).

    This should be done after a dataset has been added or removed.
    Usually this is triggered automatically and executed
    in the background.
    """
    results = [
        _run_update("sunburst charts data", _update_sunburst),
        _run_update("aggregates", _update_aggregates),
    ]
    if not all(results):
        raise CliResponseException("Failed to update all caches.")


def _update_sunburst() -> None:
    get_sunburst_service().do_background_update()


def _update_aggregates() -> None:
    get_modification_service().do_aggregates_update()


def _run_update(label: str, update: Callable[[], None]) -> bool:
    click.secho(f"Updating {label} ...", fg="yellow")
    try:
        update()
    except CacheUpdateAlreadyRunning:
        click.secho("   ... nothing to do - already running.", fg="yellow")
    except Exception as exc:
        click.secho(f"   ... failed. {exc}", fg="red", err=True)
        return False
    else:
        click.secho("   ... done.", fg="green")
    return True
