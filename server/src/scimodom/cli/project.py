import csv
import datetime

import click
from flask import Blueprint
from sqlalchemy.exc import NoResultFound

from scimodom.cli.utilities import (
    add_assembly_to_template_if_none,
    get_detection_id,
    get_modomics_id,
)
from scimodom.database.models import Project
from scimodom.services.assembly import AssemblyNotFoundError, get_assembly_service
from scimodom.services.selection import get_selection_service
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service, NoSuchUser
from scimodom.utils.dtos.project import (
    ProjectMetaDataDto,
    ProjectOrganismDto,
    ProjectSourceDto,
    ProjectTemplate,
)


project_cli = Blueprint("project", __name__)


@project_cli.cli.command(
    "create-template",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html.",
)
@click.argument("dataset_csv", type=click.Path(exists=True))
@click.option("--title", type=click.STRING, required=True, help="Project title")
@click.option("--summary", type=click.STRING, required=True, help="Project summary")
@click.option("--surname", type=click.STRING, required=True, help="Surname")
@click.option("--forename", type=click.STRING, required=True, help="Forename")
@click.option("--institution", type=click.STRING, required=True, help="Affiliation")
@click.option("--email", type=click.STRING, required=True, help="Email")
@click.option(
    "--published", type=click.DateTime(formats=["%Y-%m-%d"]), help="Date published"
)
@click.option(
    "--doi",
    type=click.STRING,
    multiple=True,
    help=(
        "List of DOI(s). Repeat in the same order as PMID(s). "
        "Use 'null' if there is a PMID w/o a DOI."
    ),
)
@click.option(
    "--pmid",
    type=click.INT,
    multiple=True,
    help=(
        "List of PMID(s). Repeat in the same order as DOI(s). "
        "Use '0' if there is a DOI w/o a PMID."
    ),
)
@click.option(
    "--use-mod-ids",
    is_flag=True,
    show_default=True,
    default=False,
    help="Do not infer modification IDs, use IDs given in DATASET_CSV.",
)
@click.option(
    "--use-method-ids",
    is_flag=True,
    show_default=True,
    default=False,
    help="Do not infer method IDs, use IDs given in DATASET_CSV.",
)
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
    use_mod_ids: bool,
    use_method_ids: bool,
):
    """Create a new project template from a list of datasets.

    \b
    DATASET_CSV is the path to a CSV file containing
    row-wise dataset metadata with the following header:
      - file: File name (bedRMod).
      - title: Dataset title.
      - rna_type: Valid RNA type.
      - modification: Valid MODOMICS short name or ID. If a dataset has
        more than 1 modification, repeat the row for this dataset and
        change the modification short name or ID. If name is given, ID
        will be inferred, else use [use-mod-ids].
      - taxa_id: Valid taxa ID.
      - cto: Cell/tissue description.
      - assembly: Valid assembly name.
      - technology: Detection technology name (tech).
      - method: Detection method name (meth) or ID. If name is given,
        ID will be inferred, else use [use-method-ids].
      - [note]: If note is present, file and title are ignored (optional).
      - [assembly_id]: If not present, this will be inferred (optional).
    Any other column will be ignored.
    """
    click.secho(
        f"Creating a new project request template from '{dataset_csv}'...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        uuid = _create_project_template(
            dataset_csv,
            title,
            summary,
            surname,
            forename,
            institution,
            email,
            published,
            doi,
            pmid,
            use_mod_ids,
            use_method_ids,
        )
        click.secho(
            f"   ... created request with ID: '{uuid}'.",
            fg="green",
        )
    except KeyError as exc:
        click.secho(
            f"Failed to create template (malformed DATASET_CSV). Missing header {exc}.",
            fg="red",
        )
        raise click.Abort()
    except ValueError as exc:
        click.secho(
            f"Failed to create template (DATASET_CSV has unexpected values). {exc}.",
            fg="red",
        )
        raise click.Abort()
    except Exception as exc:  # OSError, ValidationError
        click.secho(
            f"Failed to create template. {exc}.",
            fg="red",
        )
        raise click.Abort()


@project_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
@click.argument("request_uuid", type=click.STRING)
@click.option(
    "--add-user",
    is_flag=True,
    show_default=True,
    default=False,
    help="Add user to project. User must exists.",
)
def add_project(request_uuid: str, add_user: bool):
    """Add a new project to the database.

    REQUEST_UUID is the UUID of a project request.
    """
    file_service = get_file_service()
    project_service = get_project_service()
    assembly_service = get_assembly_service()

    try:
        with file_service.open_project_request_file(request_uuid) as fh:
            project_template_raw = fh.read()
        project_template = ProjectTemplate.model_validate_json(project_template_raw)
    except Exception as exc:  # OSError, ValidationError
        click.secho(f"Failed to read template. {exc}.", fg="red")
        raise click.Abort()

    for metadata in project_template.metadata:
        try:
            add_assembly_to_template_if_none(metadata.organism, assembly_service)
        except AssemblyNotFoundError:
            click.secho(
                (
                    f"Failed to update template. No such assembly '{metadata.organism.assembly_name}'"
                    f" for organism '{metadata.organism.taxa_id}'"
                ),
                fg="red",
            )
            raise click.Abort()

    click.secho(f"Adding project {project_template.title}...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        smid = project_service.create_project(project_template, request_uuid)
        click.secho(
            f"   ... created project with SMID: '{smid}'.",
            fg="green",
        )
    except Exception as exc:
        click.secho(
            f"Failed to create project. {exc}.",
            fg="red",
        )
        raise click.Abort()

    if add_user:
        username = project_template.contact_email
        click.secho(
            f"Adding user '{username}' to project '{smid}'...",
            fg="green",
        )
        try:
            _add_user_to_project(username, smid)
            click.secho("   ... added user.", fg="green")
        except NoSuchUser:
            click.secho("No such user. Nothing will be done.", fg="red")
            return
        except Exception as exc:
            click.secho(
                f"Failed to add user. {exc}.",
                fg="red",
            )
            raise click.Abort()


@project_cli.cli.command(
    "add-user",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html.",
)
@click.argument("username", type=click.STRING)
@click.argument("smid", type=click.STRING)
def add_user(username: str, smid: str):
    """Force add a user to a project. User must exists.

    \b
    USERNAME is the user email.
    SMID is the project ID to which this user is to be associated.
    """
    click.secho(f"Adding user '{username}' to project '{smid}'...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        _add_user_to_project(username, smid)
        click.secho("   ... user added.", fg="green")
    except NoResultFound:
        click.secho(
            f"Failed to add user. No such SMID '{smid}'.",
            fg="red",
        )
        raise click.Abort()
    except NoSuchUser as exc:
        click.secho(f"Cannot add user. {exc}.", fg="red")
        raise click.Abort()
    except Exception as exc:
        click.secho(
            f"Failed to add user. {exc}.",
            fg="red",
        )
        raise click.Abort()


@project_cli.cli.command(
    "delete",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html.",
)
@click.argument("smid", type=click.STRING)
def delete_project(smid: str):
    """Delete a project and all associated data.

    \b
    SMID is the Sci-ModoM project ID.
    Delete from the following tables:
    - selection (per dataset, if only associated with this project)
    - data_annotation
    - data
    - dataset_modification_association
    - bam_file
    - dataset
    - project_source
    - user_project_association
    - project
    - project_contact

    BAM files and gene cache associated with datasets belonging
    to this project are deleted from the file system.
    The project template metadata is deleted from the file system.
    """
    project_service = get_project_service()
    try:
        project = project_service.get_by_id(smid)
    except NoResultFound:
        click.secho(f"No such project '{smid}'.", fg="red")
        raise click.Abort()

    click.secho(
        (
            f"Deleting '{project.id}' with title '{project.title}' "
            "including data associated with the following datasets: "
        ),
        fg="green",
    )
    for dataset in project.datasets:
        click.secho(
            f"Dataset '{dataset.id}' with title '{dataset.title}'...", fg="green"
        )

    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborted!", fg="yellow")
        return

    try:
        _remove_datasets_and_selections(project)
        project_service.delete_project(project)
        click.secho("   ... deleted project", fg="green")
    except Exception as exc:
        click.secho(f"Failed to delete project '{project.id}'. {exc}", fg="red")
        raise click.Abort()


def _create_project_template(
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
    use_mod_ids: bool,
    use_method_ids: bool,
) -> str:
    project_service = get_project_service()

    metadata_list = []
    with open(dataset_csv, "r", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = [
            {
                k.strip(): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()
            }
            for row in reader
        ]
        for row in rows:
            organism = ProjectOrganismDto(
                taxa_id=row["taxa_id"],
                cto=row["cto"],
                assembly_name=row["assembly"],
                assembly_id=row["assembly_id"] if "assembly_id" in row else None,
            )
            metadata = ProjectMetaDataDto(
                rna=row["rna_type"],
                modomics_id=(
                    row["modification"]
                    if use_mod_ids
                    else get_modomics_id(row["modification"])
                ),
                tech=row["technology"],
                method_id=(
                    row["method"] if use_method_ids else get_detection_id(row["method"])
                ),
                organism=organism,
                note=(
                    row["note"]
                    if "note" in row
                    else f'file={row["file"]}, title={row["title"]}'
                ),
            )
            metadata_list.append(metadata)

    sources = []
    for dv, pv in zip(doi, pmid):
        if dv == "null":
            dv_dto = None
        else:
            dv_dto = dv
        if pv == 0:
            pv_dto = None
        else:
            pv_dto = pv
        source = ProjectSourceDto(doi=dv_dto, pmid=pv_dto)
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
    return project_service.create_project_request(project_template)


def _add_user_to_project(username: str, smid: str):
    project_service = get_project_service()
    user_service = get_user_service()
    permission_service = get_permission_service()

    project_service.get_by_id(smid)
    user = user_service.get_user_by_email(username)
    permission_service.insert_into_user_project_association(user, smid)


def _remove_datasets_and_selections(project: Project):
    selection_service = get_selection_service()
    dataset_service = get_dataset_service()
    datasets = project.datasets
    dataset_list = [dataset.id for dataset in datasets]
    for dataset in datasets:
        try:
            selection_service.delete_selections_by_dataset(dataset)
            dataset_service.delete_dataset(dataset)
            dataset_list.remove(dataset.id)
        except Exception as exc:
            msg = (
                f"Failure in handling Dataset '{dataset.id}'. "
                f"Datasets '{','.join(dataset_list)}' were not deleted."
            )
            exc.add_note(msg)
            raise
