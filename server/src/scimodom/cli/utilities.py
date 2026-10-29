import click

from sqlalchemy.exc import NoResultFound

from scimodom.services.assembly import AssemblyService, AssemblyNotFoundError
from scimodom.utils.dtos.project import ProjectOrganismDto


# This module should go; this function needs to go e.g.
# to AdminService (or ProjectImportService, or existing ProjectService).
# A new service layer would handle batch, project delete, etc. i.e.
# complex operations with several steps (commit, etc.) which must be
# handled carefully, and are not domain service-specific.


def add_assembly_to_template_if_none(
    organism: ProjectOrganismDto, assembly_service: AssemblyService
):
    """Add assembly to template.

    Assembly must exists, it is not created by default.
    If assembly ID is provided, check that it exists
    in the database.

    :param organism: Organism template
    :type organism: ProjectOrganismDto
    :param assembly_service: Assembly service
    :type assembly_service: AssemblyService
    :raises AssemblyNotFoundError: If NoResultFound for assembly
    """
    click.secho("Checking if assembly ID is defined...", fg="green")
    try:
        if organism.assembly_id is None:
            assembly = assembly_service.get_by_taxa_and_name(
                organism.taxa_id, organism.assembly_name
            )
            click.secho(
                f"updating project metadata template with assembly ID '{assembly.id}'... ",
                fg="yellow",
            )
            organism.assembly_id = assembly.id
        else:
            assembly_service.get_by_id(organism.assembly_id)
    except NoResultFound:
        raise AssemblyNotFoundError
