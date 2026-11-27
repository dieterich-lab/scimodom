"""Provide a CLI for assembly provisioning."""

import click
from flask import Blueprint

from scimodom.cli.helpers import (
    DOCS_URL,
    CliResponseException,
    confirm,
    register_cli_errors,
)
from scimodom.services.administration.assembly.provision import (
    AssemblyProvisioningError,
    get_assembly_provisioning_service,
)
from scimodom.services.assembly import (
    AssemblyNotFoundError,
    get_assembly_service,
)

assembly_cli = Blueprint("assembly", __name__)

EPILOG = f"Consult {DOCS_URL}#assembly-and-annotation"


@assembly_cli.cli.command(
    "add",
    epilog=EPILOG,
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
    help="Ensembl release",
)
@click.option(
    "--archive",
    type=click.STRING,
    required=True,
    help="Ensembl archive",
)
@click.argument(
    "taxa-id",
    type=click.INT,
    help="Must reference a valid NCBI taxon",
)
def add_assembly(
    yes: bool,
    traceback: bool,
    release: int,
    archive: str,
    taxa_id: int,
):
    """Provision assemblies.

    Set up all assemblies for TAXA_ID. For the current one,
    prepare the reference sequences and chromosomes; for
    all other assemblies, download chain files.

    The snapshot to install from Ensembl is determined by
    RELEASE and ARCHIVE. The release is validated against
    the archive, and is recorded in the assembly manifest.
    """
    provisioning_service = get_assembly_provisioning_service()

    try:
        plan = provisioning_service.plan(
            taxa_id,
            release=release,
            archive=archive,
        )
    except AssemblyNotFoundError as exc:
        raise CliResponseException(
            f"No current assembly for taxon '{taxa_id}'",
        ) from exc

    click.secho(
        f"Provisioning assembly '{plan.assembly_name}' for "
        f"taxon '{plan.taxa_id}' from "
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
    epilog=EPILOG,
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
    help="Ensembl release",
)
@click.option(
    "--archive",
    type=click.STRING,
    required=True,
    help="Ensembl archive",
)
@click.argument(
    "taxa-id",
    type=click.INT,
    help="Must reference a valid NCBI taxon",
)
def migrate_manifest(
    yes: bool, traceback: bool, release: int, archive: str, taxa_id: int
):
    """Write the assembly manifest of an existing installation.

    For assemblies created before the manifest superseded 'info.json'
    and 'release.json'. Nothing is downloaded and the current assembly
    is not touched: the manifest is written from the files already on
    the system. The legacy files are left in place.
    """
    assembly_service = get_assembly_service()

    click.secho(
        f"Writing the assembly manifest for taxon '{taxa_id}', recording "
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
            f"No legacy assembly files for taxon '{taxa_id}'. {exc}"
        ) from exc
    except FileExistsError as exc:
        raise CliResponseException(
            f"A manifest already exists for taxon '{taxa_id}'. {exc}"
        ) from exc

    click.secho(f"   ... done. Wrote '{path}'.", fg="green")
