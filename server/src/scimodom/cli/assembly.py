import click
from flask import Blueprint
from sqlalchemy.exc import NoResultFound

from scimodom.services.assembly import get_assembly_service


assembly_cli = Blueprint("assembly", __name__)


@assembly_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
@click.argument("assembly_id", type=click.INT)
def add_assembly(assembly_id: int):
    """Set up assemblies.

    All other available assemblies are added for
    the same organism.

    \b
    ASSEMBLY_ID is the current assembly (from database).
    """
    assembly_service = get_assembly_service()

    try:
        assembly = assembly_service.get_by_id(assembly_id)
    except NoResultFound:
        click.secho(
            "Failed to set up assemblies. Current assembly does not exist.",
            fg="red",
        )
        return

    click.secho(
        f"Setting up current assembly for '{assembly.name}'...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborting!", fg="yellow")
        return

    try:
        assembly_service.create_current(assembly)
        click.secho("... done!", fg="green")
    except Exception as exc:
        click.secho(
            f"Failed to set up current assembly. {exc}",
            fg="red",
        )
        return

    click.secho(
        f"Setting up assemblies for organism '{assembly.taxa_id}'...",
        fg="green",
    )
    try:
        valid_assembly_names = assembly_service.get_coord_system_versions(
            assembly.taxa_id
        )
        for assembly_name in valid_assembly_names:
            assembly_service.add_assembly(assembly.taxa_id, assembly_name)
        click.secho("... done!", fg="green")
    except Exception as exc:
        click.secho(
            f"Failed to set up all assemblies for organism. {exc}",
            fg="red",
        )
