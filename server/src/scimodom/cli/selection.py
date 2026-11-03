"""Provide a CLI for adding selections."""

import click
from flask import Blueprint

from scimodom.cli.helpers import CliResponseException, register_cli_errors, confirm
from scimodom.services.utilities import get_utilities_service
from scimodom.services.selection import get_selection_service
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
)

selection_cli = Blueprint("selection", __name__)


@selection_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html"
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.option(
    "--rna",
    required=True,
    type=click.STRING,
    help="Valid RNA type",
)
@click.option(
    "--modification",
    required=True,
    type=click.STRING,
    help="Modification (MODOMICS) short name.",
)
@click.option(
    "--taxid",
    required=True,
    type=click.INT,
    help="Valid Taxa ID.",
)
@click.option(
    "--cto",
    required=True,
    type=click.STRING,
    help="Cell/Tissue.",
)
@click.option(
    "--method-id",
    required=True,
    type=click.STRING,
    help="Method ID (from database).",
)
@click.option(
    "--technology",
    required=True,
    type=click.STRING,
    help="Technology name.",
)
def add_selection(
    yes: bool,
    traceback: bool,
    rna: str,
    modification: str,
    taxid: int,
    cto: str,
    method_id: str,
    technology: str,
):
    """Add a new selection to the database."""
    selection_service = get_selection_service()
    utilities_service = get_utilities_service()

    try:
        organism = ProjectOrganismDto(taxa_id=taxid, cto=cto, assembly_name="assembly")
        metadata = ProjectMetaDataDto(
            rna=rna,
            modomics_id=utilities_service.get_modomics_id_by_short_name(modification),
            tech=technology,
            method_id=method_id,
            organism=organism,
            note=None,
        )
    except Exception as exc:  # NoResultFound, ValidationError
        raise CliResponseException(
            f"Failed to add selection (invalid input value). {exc}"
        ) from exc

    click.secho("Adding new selection...", fg="yellow")
    confirm("Continue?", skip=yes)

    try:
        selection_service.create_selection([metadata])
    except Exception as exc:
        raise CliResponseException(f"Failed to add selection. {exc}") from exc
    click.secho("   ... added selection.", fg="green")
