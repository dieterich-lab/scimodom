import click

from sqlalchemy import select

from scimodom.database.database import get_session
from scimodom.database.models import Modomics, DetectionMethod, Dataset
from scimodom.services.setup import get_setup_service


def upsert(init: bool, **kwargs) -> None:
    """Provide a CLI function for the SetupService.

    Upsert a given table, or all default tables (defined
    in the config).

    :param init: Upsert all default tables (same as start-up)
    :type init: bool
    """
    setup_service = get_setup_service()
    if init:
        setup_service.upsert_all()
    else:
        file_name = kwargs.get("table")
        if file_name is None:
            click.secho(
                "'NoneType' object is not a valid argument for [--table].", fg="red"
            )
            return
        valid_names = setup_service.get_valid_import_file_names()
        if file_name not in valid_names:
            v = ", ".join(valid_names)
            click.secho(f"The [--table] argument needs a valid name ({v}).", fg="red")
            return

        click.secho(setup_service.get_upsert_message(file_name), fg="green")
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        setup_service.upsert_one(file_name)
    click.secho("Successfully performed INSERT... ON DUPLICATE KEY UPDATE.", fg="green")


def validate_dataset_title(ctx, param, value):
    """Validate parameter (str) length."""
    if len(value) > Dataset.title.type.length:
        raise click.BadParameter("Title cannot be longer than 255 characters!")
    return value


def add_assembly_to_template_if_none(organism, assembly_service):
    click.secho("Checking if assembly ID is defined...", fg="green")
    if organism.assembly_id is None:
        assembly_id = assembly_service.get_assembly_by_name(
            organism.taxa_id, organism.assembly_name, fail_safe=False
        )
        click.secho(
            f"Updating project metadata template with assembly ID '{assembly_id}'... ",
            fg="yellow",
        )
        organism.assembly_id = assembly_id
    else:
        assembly_service.get_assembly_by_id(organism.assembly_id)


def get_modomics_id(name):
    return (
        get_session()
        .execute(select(Modomics.id).filter_by(short_name=name))
        .scalar_one()
    )


def get_detection_id(name):
    return (
        get_session()
        .execute(select(DetectionMethod.id).filter_by(meth=name))
        .scalar_one()
    )
