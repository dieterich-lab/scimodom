"""Provide common CLI helpers."""

import sys

import click


def confirm(message: str, *, skip: bool = False) -> None:
    """Delayed confirmation option."""
    if skip:
        return

    if not _is_interactive():
        raise click.UsageError(
            "Cannot prompt for confirmation in non-interactive mode. "
            "Pass --yes to proceed",
            ctx=click.get_current_context(),
        )

    prompt = click.style(f"{message} [y/N]", fg="yellow")
    click.confirm(prompt, default=False, show_default=False, abort=True)


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


def _is_interactive() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()
