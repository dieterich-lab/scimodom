"""Provide a CLI for dataset ingestion."""

import click
from flask import Blueprint

from scimodom.database.models import Dataset
from scimodom.services.administration.ingestion import (
    ProjectTemplateError,
    get_project_ingestion_service,
)
from scimodom.services.assembly import AssemblyNotFoundError
from scimodom.services.dataset import get_dataset_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.utils.specs.enums import AnnotationSource

from scimodom.cli.helpers import (
    CliResponseException,
    register_cli_errors,
    confirm,
    trigger_charts_update,
)

dataset_cli = Blueprint("dataset", __name__)


def validate_dataset_title(ctx, param, value):
    """Validate parameter (str) length."""
    if len(value) > Dataset.title.type.length:
        raise click.BadParameter("Title cannot be longer than 255 characters.")
    return value


@dataset_cli.cli.command(
    "add",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html",
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("filename", type=click.Path(exists=True))
@click.argument("smid", type=click.STRING)
@click.argument("title", type=click.UNPROCESSED, callback=validate_dataset_title)
@click.option(
    "--assembly-id", required=True, type=click.INT, help="Assembly ID (from database)."
)
@click.option(
    "--annotation",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source.",
)
@click.option(
    "-m",
    "--modification-ids",
    default=[],
    multiple=True,
    required=True,
    type=click.INT,
    help=("Modification ID(s) (from database). Repeat to pass multiple selection IDs."),
)
@click.option(
    "-o",
    "--organism-id",
    default=None,
    required=True,
    type=click.INT,
    help="Organism ID (from database).",
)
@click.option(
    "-t",
    "--technology-id",
    default=None,
    required=True,
    type=click.INT,
    help="Technology ID (from database).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    default=False,
    help="Validate import. No database change.",
)
@click.option(
    "--eufid",
    default=None,
    required=False,
    type=click.STRING,
    help=(
        "Update data and data annotation records for existing dataset "
        "with the supplied EUFID instead of creating a new one."
    ),
)
def add_dataset(
    yes: bool,
    traceback: bool,
    filename: str,
    smid: str,
    title: str,
    assembly_id: int,
    annotation: str,
    modification_ids: tuple[int],
    organism_id: int,
    technology_id: int,
    dry_run: bool,
    eufid: str | None,
):  # noqa: D301
    """Add a new dataset or update records for an existing dataset.

    \b
    FILENAME is the path to the bedRMod (EU-formatted) file.
    SMID is the project ID to which this dataset is to be added.
    TITLE is the title of this dataset. String must be quoted.
    """
    dataset_service = get_dataset_service()

    colour = "cyan" if dry_run else "green"
    prefix = "DRY RUN - " if dry_run else ""
    msg = (
        f"Updating records for dataset '{eufid}'..."
        if eufid
        else f"Adding dataset '{title}' to project '{smid}'... "
    )
    success_msg = "update" if eufid else "create"
    click.secho(f"{prefix}{msg}", fg=colour)
    confirm("Continue?", skip=yes)

    try:
        annotation_source = AnnotationSource(annotation)
        with open(filename) as fp:
            eufid = dataset_service.import_dataset(
                fp,
                source=filename,
                project_id=smid,
                title=title,
                assembly_id=assembly_id,
                modification_ids=list(modification_ids),
                organism_id=organism_id,
                technology_id=technology_id,
                annotation_source=annotation_source,
                dry_run_flag=dry_run,
                dataset_id=eufid,
            )
        click.secho(
            f"   ... {success_msg}d dataset with EUFID '{eufid}'.",
            fg=colour,
        )
    except Exception as exc:
        raise CliResponseException(
            f"Failed to {success_msg} dataset. {exc}",
        ) from exc

    if not dry_run:
        trigger_charts_update(get_sunburst_service())


@dataset_cli.cli.command(
    "batch", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html"
)
@register_cli_errors
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument("input_directory", type=click.Path(exists=True))
@click.argument("request_uuid", type=click.STRING)
@click.option(
    "--annotation",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    default=False,
    help="Validate import. No database change.",
)
def add_dataset_in_batch(
    yes: bool,
    traceback: bool,
    input_directory: str,
    request_uuid: str,
    annotation: str,
    dry_run: bool,
):  # noqa: D301
    """Add one project and all its datasets in batch.

    All dataset files must be under INPUT_DIRECTORY, and
    must have the same annotation source. Providing files
    with different sources may not result in failure, but
    will lead to spurious database records.

    The "note" from the metadata template must contain the
    dataset file name and title as follows:
    'file=filename.bedrmod, title=title'. Metadata entries
    with the same file name are modifications of the same
    dataset, and must otherwise be identical.

    \b
    NOTE: This method cannot be used to update records
    for existing datasets.

    \b
    INPUT_DIRECTORY is the path to bedRMod (EU-formatted) files.
    REQUEST_UUID is the name (w/o extension) of a project
    template, presumably obtained by running "flask project create-template".
    """
    annotation_source = AnnotationSource(annotation)
    ingestion_service = get_project_ingestion_service()

    try:
        plan = ingestion_service.plan_batch_import(
            input_directory,
            request_uuid,
        )
    except AssemblyNotFoundError as exc:
        raise CliResponseException(f"Failed to update template. {exc}") from exc
    except ProjectTemplateError as exc:
        raise CliResponseException(f"Failed to validate request. {exc}") from exc

    colour = "cyan" if dry_run else "yellow"
    prefix = "DRY RUN - " if dry_run else ""
    click.secho(
        f"{prefix}Adding project '{plan.template.title}' and "
        f"{len(plan.datasets)} dataset(s) for {request_uuid}:",
        fg=colour,
    )
    for dataset in plan.datasets:
        click.secho(
            f"  {dataset.filename}: '{dataset.title}' "
            f"({len(dataset.modifications)} modification(s))",
            fg=colour,
        )
    if dry_run:
        return
    confirm("Continue?", skip=yes)

    try:
        result = ingestion_service.create_project(plan.template, request_uuid)
    except Exception as exc:
        raise CliResponseException(f"Failed to create project. {exc}") from exc

    click.secho(
        f"   ... created project with SMID '{result.project_id}'.",
        fg="green",
    )

    failed = []
    for outcome in ingestion_service.import_batch_datasets(
        plan, result.project_id, annotation_source
    ):
        if outcome.is_imported:
            click.secho(
                f"   ... created dataset with EUFID: '{outcome.dataset_id}' "
                f"({outcome.dataset.filename}).",
                fg="green",
            )
        else:
            failed.append(outcome)
            click.secho(
                f"Failed to create dataset '{outcome.dataset.filename}'. "
                f"{outcome.error}... Skipping!",
                fg="red",
            )
    imported = len(plan.datasets) - len(failed)
    click.secho(f"   ... done ({imported}/{len(plan.datasets)} datasets).", fg="green")

    if imported:
        trigger_charts_update(get_sunburst_service())
    if failed:
        raise CliResponseException(
            f"Project '{result.project_id}' was created, but {len(failed)} dataset(s) "
            f"failed: {', '.join(o.dataset.filename for o in failed)}. "
            "Add them with 'flask dataset add'."
        )
