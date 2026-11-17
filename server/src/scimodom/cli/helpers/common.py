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


def trigger_cache_update(external_service) -> None:
    """Trigger the update of all caches in the background.

    :param external_service: An External service instance
    """
    click.secho("Triggering cache update in the background ...", fg="yellow")
    try:
        external_service.trigger_cache_update()
    except Exception as exc:
        click.secho(
            f"Warning: failed to trigger cache update. {exc}. "
            "Run 'flask cache update'.",
            fg="yellow",
        )
    else:
        click.secho("   ... done.", fg="green")


def _is_interactive() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()
