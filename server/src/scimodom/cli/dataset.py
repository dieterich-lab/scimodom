"""Provide a CLI for dataset ingestion."""

import click
from flask import Blueprint

from scimodom.database.models import Dataset
from scimodom.services.administration.ingestion import (
    ProjectTemplateError,
    get_project_ingestion_service,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyNotFoundError
from scimodom.services.dataset import get_dataset_service
from scimodom.services.sunburst import get_sunburst_service

from scimodom.cli.helpers import (
    audited,
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
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management",
)
@register_cli_errors
@audited("dataset.add")
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument(
    "smid",
    type=click.STRING,
    help=(
        "Must reference an existing Sci-ModoM project ID. "
        "The dataset will be added to this project"
    ),
)
@click.argument(
    "title",
    type=click.UNPROCESSED,
    callback=validate_dataset_title,
    help="Dataset title. Use quote",
)
@click.argument(
    "filename", type=click.Path(exists=True), help="bedRMod (EU-formatted) file"
)
@click.option(
    "--assembly-id",
    required=True,
    type=click.INT,
    help="Must reference an existing assembly ID",
)
@click.option(
    "--rna-type",
    required=True,
    type=click.STRING,
    help="Must reference an existing RNA type record",
)
@click.option(
    "-m",
    "--modification-ids",
    default=[],
    multiple=True,
    required=True,
    type=click.INT,
    help=(
        "Must reference existing modification ID(s). Repeat to pass multiple selection IDs"
    ),
)
@click.option(
    "-o",
    "--organism-id",
    default=None,
    required=True,
    type=click.INT,
    help="Must reference an existing organism ID",
)
@click.option(
    "-t",
    "--technology-id",
    default=None,
    required=True,
    type=click.INT,
    help="Must reference an existing technology ID",
)
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    default=False,
    help="Validate import (no change)",
)
@click.option(
    "--eufid",
    default=None,
    required=False,
    type=click.STRING,
    help=(
        "Replace data and annotation records for the supplied EUFID. "
        "Only the records change; organism, technology, modifications "
        "and stored dataset metadata must be identical to the existing "
        "dataset. Use with --dry-run to validate the update."
    ),
)
def add_dataset(
    yes: bool,
    traceback: bool,
    smid: str,
    title: str,
    filename: str,
    assembly_id: int,
    rna_type: str,
    modification_ids: tuple[int],
    organism_id: int,
    technology_id: int,
    dry_run: bool,
    eufid: str | None,
):
    """Add a new dataset or update records for an existing dataset.

    An update (--eufid) replaces all records of the dataset; its metadata
    and modifications cannot be changed.
    """
    dataset_service = get_dataset_service()

    colour = "cyan" if dry_run else "green"
    prefix = "DRY RUN - " if dry_run else ""
    msg = (
        f"Updating records for dataset '{eufid}'..."
        if eufid
        else f"Adding dataset '{title}' to project '{smid}'... "
    )
    completed_action = (
        "validated update for dataset"
        if dry_run and eufid
        else (
            "validated dataset"
            if dry_run
            else ("updated dataset" if eufid else "created dataset")
        )
    )
    failed_action = (
        "validate dataset update"
        if dry_run and eufid
        else (
            "validate dataset"
            if dry_run
            else ("update dataset" if eufid else "create dataset")
        )
    )
    click.secho(f"{prefix}{msg}", fg=colour)
    confirm("Continue?", skip=yes)

    try:
        annotation_source = AnnotationService.get_annotation_source(rna_type)
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
            f"   ... {completed_action} with EUFID '{eufid}'.",
            fg=colour,
        )
    except Exception as exc:
        raise CliResponseException(
            f"Failed to {failed_action}. {exc}",
        ) from exc

    if not dry_run:
        trigger_charts_update(get_sunburst_service())


@dataset_cli.cli.command(
    "batch",
    epilog="Consult https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management",
)
@register_cli_errors
@audited("dataset.batch")
@click.option("--yes", is_flag=True, help="Confirm the action without prompting")
@click.option("--traceback", is_flag=True, help="Show traceback")
@click.argument(
    "request_uuid",
    type=click.STRING,
    help=(
        "The name (w/o extension) of a project template, "
        "presumably obtained by running `flask project create-template`"
    ),
)
@click.argument(
    "input_directory",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Directory with bedRMod (EU-formatted) files",
)
@click.option(
    "--dry-run",
    is_flag=True,
    show_default=True,
    default=False,
    help="Validate import (no change)",
)
def add_dataset_in_batch(
    yes: bool,
    traceback: bool,
    request_uuid: str,
    input_directory: str,
    dry_run: bool,
):
    """Add one project and all its datasets in batch.

    All dataset files must be under INPUT_DIRECTORY.
    The RNA type (and thus the annotation source) of a dataset is
    taken from the metadata template, and must be the same for all
    modifications of a dataset. The files are assumed to be
    consistent with the template: a dataset whose records do not
    match is rejected at import.

    The "note" from the metadata template must contain the
    dataset file name and title as follows:
    'file=filename.bedrmod, title=title'. Metadata entries
    with the same file name are modifications of the same
    dataset, and must otherwise be identical.

    NOTE: This method cannot be used to update records for
    existing datasets, see `dataset add`.
    """
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
    for outcome in ingestion_service.import_batch_datasets(plan, result.project_id):
        if outcome.is_imported:
            click.secho(
                f"   ... created dataset with EUFID '{outcome.dataset_id}' "
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
