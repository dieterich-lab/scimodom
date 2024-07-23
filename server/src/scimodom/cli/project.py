import csv
import datetime
from pathlib import Path

import click
from sqlalchemy.exc import NoResultFound

from scimodom.cli.utilities import (
    add_assembly_to_template_if_none,
    get_detection_id,
    get_modomics_id,
)
from scimodom.services.assembly import AssemblyNotFoundError, get_assembly_service
from scimodom.services.permission import get_permission_service
from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service, NoSuchUser
from scimodom.utils.project_dto import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
    ProjectSourceDto,
    ProjectTemplate,
)


def add_project(
    project_template: ProjectTemplate, request_uuid: str, add_user: bool = True
) -> None:
    """Provide a CLI function to add a new project.

    :param project_template: Project template
    :type project_template: ProjectTemplate
    :param request_uuid: UUID of request
    :type request_uuid: str
    :param add_user: Associate user and newly created project
    :type add_user: bool
    """
    project_service = get_project_service()
    assembly_service = get_assembly_service()

    for metadata in project_template.metadata:
        try:
            add_assembly_to_template_if_none(metadata.organism, assembly_service)
        except AssemblyNotFoundError:
            click.secho(
                f"No such assembly '{metadata.organism.assembly_id}'... Aborting!",
                fg="red",
            )
            return
    click.secho(f"Adding project {project_template.title}...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    try:
        smid = project_service.create_project(project_template, request_uuid)
        click.secho(
            f"Created project with SMID '{smid}'... done!",
            fg="green",
        )
    except Exception as exc:
        click.secho(
            f"Failed to create project: {exc}... Aborting!",
            fg="red",
        )
        return
    if add_user:
        add_user_to_project(project_template.contact_email, smid)


def add_user_to_project(username: str, smid: str) -> None:
    """Provide a CLI function to add a user to a project.

    :param username: Username (email)
    :type username: str
    :param smid: SMID
    :type smid: str
    """
    project_service = get_project_service()
    user_service = get_user_service()
    permission_service = get_permission_service()
    click.secho(f"Adding user '{username}' to project '{smid}'...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    try:
        project_service.get_by_id(smid)
    except NoResultFound:
        click.secho(
            f"Unrecognised SMID {smid}... Aborting!",
            fg="red",
        )
        return
    try:
        user = user_service.get_user_by_email(username)
    except NoSuchUser:
        click.secho(f"No such user with {username}... Aborting!", fg="red")
        return
    else:
        permission_service.insert_into_user_project_association(user, smid)
        click.secho("Added user to project...", fg="green")
    click.secho("... done!", fg="green")


def create_project_template(
    dataset_csv: str,
    title: str,
    summary: str,
    surname: str,
    forename: str,
    institution: str,
    email: str,
    published: datetime.date,
    doi: list[str],
    pmid: list[int],
    method_id: int | None = None,
) -> None:
    """Provide a CLI function to create a project template
    request from a tabulated list of datasets.

    dataset_csv, title, summary, surname, forename, institution, email, published, doi, pmid, method_id
    :param username: Username (email)
    :type username: str
    :param smid: SMID
    :type smid: str
    """
    project_service = get_project_service()

    click.secho(
        f"Creating project template request using '{dataset_csv}'...", fg="green"
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    try:
        metadata_list = []
        with open(dataset_csv, "r") as fh:
            for row in csv.DictReader(fh):
                organism = ProjectOrganismDto(
                    taxa_id=row["taxa_id"],
                    cto=row["cto"],
                    assembly_name=row["assembly"],
                    assembly_id=row["assembly_id"] if "assembly_id" in row else None,
                )
                metadata = ProjectMetaDataDto(
                    rna=row["rna_type"],
                    modomics_id=get_modomics_id(row["modification"]),
                    tech=row["technology"],
                    method_id=get_detection_id(row["method"])
                    if "method" in row
                    else method_id,
                    organism=organism,
                    note=row["note"]
                    if "note" in row
                    else f'file={row["file"]}, title={row["title"]}',
                )
                metadata_list.append(metadata)

        sources = []
        for dv, pv in zip(doi, pmid):
            if dv == "null":
                dv = None
            if pv == 0:
                pv = None
            source = ProjectSourceDto(doi=dv, pmid=pv)
            sources.append(source)

        project_template = ProjectTemplate(
            title=title,
            summary=summary,
            contact_name=f"{surname}, {forename}",
            contact_institution=institution,
            contact_email=email,
            date_published=published,
            external_sources=sources,
            metadata=metadata_list,
        )
    except Exception as exc:
        click.secho(
            f"Validation error, failed to create template: {exc}. Aborting!",
            fg="red",
        )
        return

    uuid = project_service.create_project_request(project_template)
    click.secho(
        f"Created request '{uuid}'... ",
        fg="green",
    )
