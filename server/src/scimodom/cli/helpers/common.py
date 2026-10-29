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
