"""Provide a CLI for assembly provisioning."""

import click
from flask import Blueprint

from scimodom.services.administration.assembly.provision import (
    AssemblyProvisioningError,
    get_assembly_provisioning_service,
)
from scimodom.services.assembly import (
    AssemblyNotFoundError,
    get_assembly_service,
)
from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
)

assembly_cli = Blueprint("assembly", __name__)


@assembly_cli.cli.command(
    "add",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#assembly-and-annotation",
)
@register_cli_errors
@click.option(
    "--yes",
    is_flag=True,
    help="Confirm the action without prompting",
)
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.option(
    "--release",
    type=click.INT,
    required=True,
    help="Ensembl release to obtain the reference files from, e.g. 110.",
)
@click.option(
    "--archive",
    type=click.STRING,
    required=True,
    help="Ensembl archive to obtain the reference files from, e.g. 'jul2023'.",
)
@click.argument(
    "assembly_id", type=click.INT, help="Database record for the current assembly"
)
def add_assembly(
    yes: bool,
    traceback: bool,
    release: int,
    archive: str,
    assembly_id: int,
):
    """Provision assemblies.

    Set up the current assembly for ASSEMBLY_ID and
    all other available assemblies for the same organism.

    The snapshot to install has to be stated: nothing is inferred from
    the code, and there is no manifest to read it from yet. The release
    is validated against the archive before anything is downloaded, and
    both are recorded in the assembly manifest.
    """
    provisioning_service = get_assembly_provisioning_service()

    try:
        plan = provisioning_service.plan(assembly_id, release=release, archive=archive)
    except AssemblyNotFoundError as exc:
        raise CliResponseException(f"Assembly '{assembly_id}' not found.") from exc

    click.secho(
        f"Provisioning assemblies for organism '{plan.taxa_id}' from "
        f"Ensembl release {plan.release} ({plan.archive}). "
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


@assembly_cli.cli.command(
    "migrate-manifest",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#assembly-and-annotation",
)
@register_cli_errors
@click.option(
    "--yes",
    is_flag=True,
    help="Confirm the action without prompting",
)
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.option(
    "--release",
    type=click.INT,
    required=True,
    help="Ensembl release the existing files were obtained from, e.g. 110.",
)
@click.option(
    "--archive",
    type=click.STRING,
    required=True,
    help="Ensembl archive the existing files were obtained from, e.g. 'jul2023'.",
)
@click.argument("taxa_id", type=click.INT, help="Organism for which to write it")
def migrate_manifest(
    yes: bool, traceback: bool, release: int, archive: str, taxa_id: int
):
    """Write the assembly manifest of an existing installation.

    For assemblies created before the manifest superseded 'info.json'
    and 'release.json'. Nothing is downloaded and the current assembly
    is not touched: the manifest is written from the files already on
    the system, with the ownership and mode of every other assembly
    file, so there is no need to re-run 'flask assembly add'.

    The legacy files are left in place; remove them once the
    application has been verified against the manifest.
    """
    assembly_service = get_assembly_service()

    click.secho(
        f"Writing the assembly manifest for organism '{taxa_id}', recording "
        f"Ensembl release {release} ({archive}) as the source of the existing "
        "reference files...",
        fg="yellow",
    )
    click.secho(
        "Check that these match the files actually installed: they are "
        "recorded as fact and are not verified against Ensembl.",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        path = assembly_service.migrate_manifest(taxa_id, release, archive)
    except FileNotFoundError as exc:
        raise CliResponseException(
            f"No legacy assembly files for organism '{taxa_id}'. {exc}"
        ) from exc
    except FileExistsError as exc:
        raise CliResponseException(
            f"A manifest already exists for organism '{taxa_id}'. {exc}"
        ) from exc

    click.secho(f"   ... done. Wrote '{path}'.", fg="green")
