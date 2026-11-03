"""Provide a CLI for project administration."""

import datetime

import click
from flask import Blueprint
from sqlalchemy.exc import NoResultFound

from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
    trigger_charts_update,
)
from scimodom.services.administration.deletion import (
    ProjectDeletionError,
    get_project_deletion_service,
)
from scimodom.services.administration.ingestion import (
    ProjectRequestInfo,
    ProjectTemplateError,
    UserAssociationError,
    get_project_ingestion_service,
)
from scimodom.services.assembly import AssemblyNotFoundError
from scimodom.services.sunburst import get_sunburst_service
from scimodom.services.user import NoSuchUser

project_cli = Blueprint("project", __name__)


@project_cli.cli.command(
    "create-template",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
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
    yes: bool,
    traceback: bool,
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
):  # noqa: D301
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
    ingestion_service = get_project_ingestion_service()

    try:
        template = ingestion_service.build_template(
            dataset_csv,
            ProjectRequestInfo(
                title=title,
                summary=summary,
                surname=surname,
                forename=forename,
                institution=institution,
                email=email,
                published=published,
                doi=tuple(doi),
                pmid=tuple(pmid),
            ),
            use_mod_ids=use_mod_ids,
            use_method_ids=use_method_ids,
        )
    except ProjectTemplateError as exc:
        raise CliResponseException(f"Failed to create template. {exc}") from exc

    click.secho(
        f"Creating a new project request template from '{dataset_csv}' "
        f"({len(template.metadata)} metadata entries)...",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        uuid = ingestion_service.save_request(template)
    except Exception as exc:  # OSError
        raise CliResponseException(f"Failed to create template. {exc}") from exc
    click.secho(f"   ... created request with ID: '{uuid}'.", fg="green")


@project_cli.cli.command(
    "add", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html"
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("request_uuid", type=click.STRING)
@click.option(
    "--add-user",
    is_flag=True,
    show_default=True,
    default=False,
    help="Add user to project. User must exists.",
)
def add_project(
    yes: bool, traceback: bool, request_uuid: str, add_user: bool
):  # noqa: D301
    """Add a new project to the database.

    \b
    REQUEST_UUID is the UUID of a project request.
    """
    ingestion_service = get_project_ingestion_service()

    try:
        template = ingestion_service.load_template(request_uuid)
    except ProjectTemplateError as exc:
        raise CliResponseException(str(exc)) from exc
    except AssemblyNotFoundError as exc:
        raise CliResponseException(f"Failed to update template. {exc}") from exc

    click.secho(f"Adding project {template.title}...", fg="yellow")
    confirm("Continue?", skip=yes)

    try:
        result = ingestion_service.create_project(
            template, request_uuid, add_user=add_user
        )
    except UserAssociationError as exc:
        click.secho(f"   ... created project with SMID '{exc.project_id}'.", fg="green")
        raise CliResponseException(str(exc)) from exc
    except Exception as exc:
        raise CliResponseException(f"Failed to create project. {exc}") from exc

    click.secho(f"   ... created project with SMID: '{result.project_id}'.", fg="green")
    if result.user_added is True:
        click.secho(
            f"   ... added user '{template.contact_email}' to the project.", fg="green"
        )
    elif result.user_added is False:
        click.secho(
            f"No such user '{template.contact_email}'. No user was added.",
            fg="yellow",
        )


@project_cli.cli.command(
    "add-user",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("username", type=click.STRING)
@click.argument("smid", type=click.STRING)
def add_user(yes: bool, traceback: bool, username: str, smid: str):  # noqa: D301
    """Force add a user to a project. User must exists.

    \b
    USERNAME is the user email.
    SMID is the project ID to which this user is to be associated.
    """
    click.secho(
        f"Adding user '{username}' to project '{smid}'. If exists, nothing is done...",
        fg="yellow",
    )
    confirm("Continue?", skip=yes)

    try:
        get_project_ingestion_service().add_user_to_project(username, smid)
    except NoResultFound as exc:
        raise CliResponseException(
            f"Failed to add user. No such SMID '{smid}'."
        ) from exc
    except NoSuchUser as exc:
        raise CliResponseException(f"Cannot add user. {exc}") from exc
    except Exception as exc:
        raise CliResponseException(f"Failed to add user. {exc}") from exc
    click.secho("   ... done.", fg="green")


@project_cli.cli.command(
    "delete",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("smid", type=click.STRING)
def delete_project(yes: bool, traceback: bool, smid: str):  # noqa: D301
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
    deletion_service = get_project_deletion_service()
    try:
        plan = deletion_service.plan(smid)
    except NoResultFound as exc:
        raise CliResponseException(f"Project '{smid}' not found.") from exc

    click.secho(
        (
            f"Deleting '{plan.project_id}' with title '{plan.title}' "
            "including data associated with the following datasets: "
        ),
        fg="yellow",
    )
    for dataset in plan.datasets:
        click.secho(
            f"Dataset '{dataset.id}' with title '{dataset.title}'...", fg="yellow"
        )
    confirm("Continue?", skip=yes)

    try:
        result = deletion_service.execute(plan)
    except ProjectDeletionError as exc:
        # what was deleted stays deleted, update the charts accordingly
        if exc.deleted_dataset_ids:
            trigger_charts_update(get_sunburst_service())
        raise CliResponseException(
            f"Failed to delete project '{plan.project_id}'. {exc} "
            "Run the command again to resume."
        ) from exc
    except Exception as exc:
        raise CliResponseException(
            f"Failed to delete project '{plan.project_id}'. {exc}"
        ) from exc

    click.secho(
        f"   ... deleted project and {len(result.deleted_dataset_ids)} dataset(s).",
        fg="green",
    )
    trigger_charts_update(get_sunburst_service())
