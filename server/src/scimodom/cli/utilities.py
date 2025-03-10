import click

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    DetectionMethod,
    Modomics,
)
from scimodom.services.assembly import AssemblyService, AssemblyNotFoundError
from scimodom.utils.dtos.project import (
    ProjectOrganismDto,
)


def validate_dataset_title(ctx, param, value):
    """Validate parameter (str) length."""
    if len(value) > Dataset.title.type.length:
        raise click.BadParameter("Title cannot be longer than 255 characters!")
    return value


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


def get_modomics_id(name) -> str:
    """Retrieve MODOMICS ID from short name.

    :param name: MODOMICS short name
    :type name: str
    :raises ValueError: If NoResultFound
    :return: MODOMICS ID
    :rtype: str
    """
    try:
        return (
            get_session()
            .execute(select(Modomics.id).filter_by(short_name=name))
            .scalar_one()
        )
    except NoResultFound:
        raise ValueError(f"No such modification '{name}'.")


def get_detection_id(name) -> str:
    """Retrieve detection method ID from name (meth).

    :param name: Method name (meth)
    :type name: str
    :raises ValueError: If NoResultFound
    :return: DetectionMethod ID
    :rtype: str
    """
    try:
        return (
            get_session()
            .execute(select(DetectionMethod.id).filter_by(meth=name))
            .scalar_one()
        )
    except NoResultFound:
        raise ValueError(f"No such detection method '{name}'.")
