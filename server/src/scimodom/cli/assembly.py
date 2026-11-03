"""Provide a CLI for assembly provisioning."""

import click
from flask import Blueprint

from scimodom.services.administration.assembly.provision import (
    AssemblyProvisioningError,
    get_assembly_provisioning_service,
)
from scimodom.services.assembly import AssemblyNotFoundError

from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
)

assembly_cli = Blueprint("assembly", __name__)


@assembly_cli.cli.command(
    "add",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option(
    "--yes",
    is_flag=True,
    help="Confirm the action without prompting",
)
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("assembly_id", type=click.INT)
def add_assembly(yes: bool, traceback: bool, assembly_id: int):  # noqa: D301
    """Provision assemblies.

    Set up the current assembly for ASSEMBLY_ID, and
    all other available assemblies for the same organism.

    \b
    ASSEMBLY_ID is the database record for the current assembly.
    """
    provisioning_service = get_assembly_provisioning_service()

    try:
        plan = provisioning_service.plan(assembly_id)
    except AssemblyNotFoundError as exc:
        raise CliResponseException(f"Assembly '{assembly_id}' not found.") from exc

    click.secho(
        f"Provisioning assemblies for organism '{plan.taxa_id}'. "
        "This will take a few minutes to download data...",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        result = provisioning_service.execute(plan)
    except AssemblyProvisioningError as exc:
        raise CliResponseException(str(exc)) from exc

    click.secho(
        f"   ... done with current assembly '{result.current_assembly_name}'.",
        fg="green",
    )
    for name in result.added:
        click.secho(f"   ... done with {name}.", fg="green")
    if result.failed:
        for name, exc in result.failed.items():
            click.secho(f"Failed to provision {name}. {exc}", fg="red")
        raise CliResponseException(
            f"Provisioning failed for {len(result.failed)} assembly(ies). "
            "Run the command again to retry."
        )
    click.secho("   ... done.", fg="green")
