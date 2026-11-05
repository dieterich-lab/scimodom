"""Provide a CLI for adding selections."""

import click
from flask import Blueprint

from scimodom.cli.helpers import (
    audited,
    CliResponseException,
    register_cli_errors,
    confirm,
)
from scimodom.services.utilities import get_utilities_service
from scimodom.services.selection import get_selection_service
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
)

selection_cli = Blueprint("selection", __name__)


@selection_cli.cli.command(
    "add",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management",
)
@register_cli_errors
@audited("selection.add")
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.option(
    "--rna-type",
    required=True,
    type=click.STRING,
    help="Must reference an existing RNA type record",
)
@click.option(
    "--modification",
    required=True,
    type=click.STRING,
    help="Must reference a MODOMICS short name",
)
@click.option(
    "--taxid",
    required=True,
    type=click.INT,
    help="Must reference a valid NCBI taxon",
)
@click.option(
    "--cto",
    required=True,
    type=click.STRING,
    help="Cell, tissue or organ. Use quote",
)
@click.option(
    "--method",
    required=True,
    type=click.STRING,
    help="Must reference a valid detection method. Use quote",
)
@click.option(
    "--technology",
    required=True,
    type=click.STRING,
    help="Detection technology. Use quote",
)
def add_selection(
    yes: bool,
    traceback: bool,
    rna_type: str,
    modification: str,
    taxid: int,
    cto: str,
    method: str,
    technology: str,
):
    """Add a new selection to the database."""
    selection_service = get_selection_service()
    utilities_service = get_utilities_service()

    try:
        organism = ProjectOrganismDto(
            taxa_id=taxid,
            cto=cto,
            assembly_name="assembly",
        )
        metadata = ProjectMetaDataDto(
            rna=rna_type,
            modomics_id=utilities_service.get_modomics_id_by_short_name(modification),
            tech=technology,
            method_id=utilities_service.get_method_id_by_name(method),
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
