import click

from scimodom.services.assembly import (
    AssemblyNotFoundError,
    AssemblyVersionError,
    AssemblyAbortedError,
    get_assembly_service,
)


def add_assembly(**kwargs) -> None:
    """Provide a CLI function to manage assemblies.

    If "assembly_id" is given, prepare an assembly
    for the latest version, else add an alternative
    assembly using "taxa_id" and "name".
    """
    assembly_service = get_assembly_service()

    assembly_id = kwargs.get("assembly_id", None)
    if assembly_id:
        assembly = assembly_service.get_assembly_by_id(assembly_id)
        click.secho(
            f"Preparing assembly for {assembly.name}...",
            fg="green",
        )
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        try:
            assembly_service.prepare_assembly_for_version(assembly_id)
        except FileExistsError:
            click.secho(
                "Assembly directory already exists... Aborting!",
                fg="red",
            )
            return
        except AssemblyVersionError as exc:
            click.secho(
                f"Cannot create assembly for this database version: {exc}",
                fg="red",
            )
            return
        except AssemblyAbortedError as exc:
            click.secho(f"Failed to prepare assembly: {exc}", fg="red")
            return
        click.secho("... done!", fg="green")
    else:
        assembly_name = kwargs["assembly_name"]
        taxa_id = kwargs["taxa_id"]
        click.secho(
            f"Adding an alternative assembly for {assembly_name}. If this assembly already exists, nothing will be done...",
            fg="green",
        )
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        try:
            assembly = assembly_service.get_assembly_by_name(taxa_id, assembly_name)
        except AssemblyNotFoundError as exc:
            click.secho(f"Cannot add alternative assembly: {exc}", fg="red")
        except AssemblyAbortedError as exc:
            click.secho(f"Failed to add alternative assembly: {exc}", fg="red")
            return
        click.secho(f"... done! Assembly ID is {assembly.id}.", fg="green")
