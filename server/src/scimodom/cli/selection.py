import click
from flask import Blueprint

from scimodom.cli.utilities import (
    get_modomics_id,
)
from scimodom.services.selection import get_selection_service
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
)


selection_cli = Blueprint("selection", __name__)


@selection_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
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
    rna: str,
    modification: str,
    taxid: int,
    cto: str,
    method_id: str,
    technology: str,
) -> None:
    """Add a new selection to the database."""
    selection_service = get_selection_service()

    try:
        organism = ProjectOrganismDto(taxa_id=taxid, cto=cto, assembly_name="assembly")
        metadata = ProjectMetaDataDto(
            rna=rna,
            modomics_id=get_modomics_id(modification),
            tech=technology,
            method_id=method_id,
            organism=organism,
            note=None,
        )
    except Exception as exc:
        click.secho(
            f"Failed to add selection (invalid input value). {exc}.",
            fg="red",
        )
        raise click.Abort()

    click.secho("Adding new selection...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        selection_service.create_selection([metadata])
        click.secho("   ... added selection.", fg="green")
    except Exception as exc:
        click.secho(
            f"Failed to add selection. {exc}.",
            fg="red",
        )
        raise click.Abort()
