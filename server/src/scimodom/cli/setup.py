"""Provide CLI commands for reference-data setup."""

import click
from flask import Blueprint

from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
)
from scimodom.services.setup import get_setup_service

setup_cli = Blueprint("setup", __name__)


@setup_cli.cli.command(
    "upsert",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#data-import",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument(
    "filename",
    nargs=-1,
    help=(
        "Import one or more files (base name + extension) defined in SetupService "
        "and located under IMPORT_PATH or HOST_IMPORT_DIR."
    ),
)
def upsert(yes: bool, traceback: bool, filename: tuple[str, ...]):
    """Perform an INSERT... ON DUPLICATE KEY UPDATE (database initialization).

    If no FILENAME is given, a default import is performed.
    The command is idempotent. It must be run after the database schema
    was created or upgraded, and whenever the import files change.
    The app does not do this on startup.
    """
    try:
        setup_service = get_setup_service()
        if not filename:
            confirm("Initialize (default)?", skip=yes)
            setup_service.upsert_all()
        else:
            names = list(filename)
            invalid = [
                name for name in names if not setup_service.is_valid_import_file(name)
            ]
            if invalid:
                raise CliResponseException(
                    f"Unknown import file(s): {', '.join(invalid)}. "
                    f"Valid names are: {', '.join(setup_service.get_valid_import_file_names())}."
                )
            confirm(f"Upsert {len(names)} import file(s)?", skip=yes)
            for name in names:
                setup_service.upsert_one(name)
    except (CliResponseException, click.ClickException, click.Abort):
        raise
    except Exception as exc:
        raise CliResponseException(f"Failed to update database. {exc}") from exc
    click.secho("   ... done.", fg="green")
