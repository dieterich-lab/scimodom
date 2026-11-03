"""Provide common CLI helpers."""

import sys

import click


def confirm(message: str, *, skip: bool = False) -> None:
    """Delayed confirmation option."""
    if skip:
        return

    if sys.stdin is None or not sys.stdin.isatty():
        raise click.UsageError(
            "Cannot prompt for confirmation in non-interactive mode. "
            "Pass --yes to proceed",
            ctx=click.get_current_context(),
        )

    click.confirm(
        click.style(message, fg="yellow"),
        default=False,
        abort=True,
    )


def trigger_charts_update(sunburst_service) -> None:
    """Trigger the charts update in the background.

    :param sunburst_service: A Sunburst service instance
    """
    click.secho("Triggering charts update in the background ...", fg="yellow")
    try:
        sunburst_service.trigger_background_update()
    except Exception as exc:
        click.secho(
            f"Warning: failed to trigger charts update. {exc}. "
            "Run 'flask charts sunburst-update'.",
            fg="yellow",
        )
    else:
        click.secho("   ... done.", fg="green")
