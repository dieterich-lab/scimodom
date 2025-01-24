from collections import defaultdict
from pathlib import Path
import re

import click
from flask import Blueprint
from sqlalchemy import select

from scimodom.database.database import get_session
from scimodom.database.models import (
    DetectionTechnology,
    Organism,
    Modification,
)
from scimodom.cli.utilities import (
    add_assembly_to_template_if_none,
    validate_dataset_title,
)

from scimodom.services.assembly import AssemblyNotFoundError, get_assembly_service
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.project import get_project_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.utils.dtos.project import (
    ProjectTemplate,
)
from scimodom.utils.specs.enums import AnnotationSource


dataset_cli = Blueprint("dataset", __name__)


@dataset_cli.cli.command(
    "add",
    epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html.",
)
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
    help="Validate import. No database change. Overrides [--eufid].",
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
) -> None:
    """Add a new dataset or update records for an existing dataset.

    \b
    FILENAME is the path to the bedRMod (EU-formatted) file.
    SMID is the project ID to which this dataset is to be added.
    TITLE is the title of this dataset. String must be quoted.
    """
    dataset_service = get_dataset_service()

    colour = "green"
    msg = f"Adding dataset '{title}' to project with SMID '{smid}'... "
    if dry_run:
        msg = f"DRY RUN: {msg}"
        colour = "cyan"
    elif eufid is not None:
        msg = f"Updating data records for dataset '{eufid}'..."
    click.secho(msg, fg=colour)
    click.secho("Continue [y/n]?", fg=colour)
    c = click.getchar()
    if c not in ["y", "Y"]:
        click.secho("Aborting!", fg="yellow")
        return

    try:
        annotation_source = AnnotationSource(annotation)
        with open(filename) as fp:
            eufid = dataset_service.import_dataset(
                fp,
                source=filename,
                smid=smid,
                title=title,
                assembly_id=assembly_id,
                modification_ids=list(modification_ids),
                organism_id=organism_id,
                technology_id=technology_id,
                annotation_source=annotation_source,
                dry_run_flag=dry_run,
                eufid=eufid,
            )
        click.secho(
            f"Created or updated dataset with EUFID: '{eufid}'.",
            fg=colour,
        )
    except Exception as exc:
        click.secho(
            f"Failed to create or update dataset. {exc}.",
            fg="red",
        )
        return

    if not dry_run:
        try:
            click.secho("Triggering charts update in the background ...", fg="green")
            _so_sunburst_update()
        except Exception as exc:
            click.secho(
                f"Failed to update charts. {exc}.",
                fg="red",
            )


@dataset_cli.cli.command(
    "batch", epilog="Check docs at https://dieterich-lab.github.io/scimodom/flask.html."
)
@click.argument("input_directory", type=click.Path(exists=True))
@click.argument("request_uuid", type=click.STRING)
@click.option(
    "--annotation",
    required=True,
    type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
    help="Annotation source.",
)
def add_dataset_in_batch(input_directory: str, request_uuid: str, annotation: str):
    """Add one project and all its datasets in batch w/o confirmation.

    All dataset files must be under INPUT_DIRECTORY, and
    must have the same annotation source. Providing files
    with different sources may not result in failure, but
    will lead to spurious database records.

    The "note" from the metadata template must contain the
    dataset file name and title as follows:
    'file=filename.bedrmod, title=title'.

    There is no [--dry-run] option.
    This method cannot be used to update records for existing datasets.

    \b
    INPUT_DIRECTORY is the path to bedRMod (EU-formatted) files.
    REQUEST_UUID is the name (w/o extension) of a project
    template, presumably obtained by running "flask project create-template".
    """
    regexp = re.compile(r"(file=)(.*),\s*(title=)(.*)")
    annotation_source = AnnotationSource(annotation)
    assembly_service = get_assembly_service()
    project_service = get_project_service()
    dataset_service = get_dataset_service()

    try:
        filename_modification_association = defaultdict(list)
        project_template = _validate_input(request_uuid)
        for metadata in project_template.metadata:
            add_assembly_to_template_if_none(metadata.organism, assembly_service)
            filename = regexp.search(metadata.note).group(2).strip()
            filename_modification_association[filename].append(
                (metadata.rna, metadata.modomics_id)
            )
    except Exception as exc:
        click.secho(
            f"Failed to validate project request. {exc}.",
            fg="red",
        )
        return
    except AssemblyNotFoundError:
        click.secho(
            (
                f"Failed to update template. No such assembly '{metadata.organism.assembly_name}'"
                f" for organism '{metadata.organism.taxa_id}'"
            ),
            fg="red",
        )
        return

    try:
        smid = project_service.create_project(project_template, request_uuid)
        click.secho(
            f"Created project with SMID: '{smid}'.",
            fg="green",
        )
    except Exception as exc:
        click.secho(
            f"Failed to create project. {exc}.",
            fg="red",
        )
        return

    visited = set()
    for metadata in project_template.metadata:
        filename = regexp.search(metadata.note).group(2).strip()
        file_path = Path(input_directory, filename)
        title = regexp.search(metadata.note).group(4).strip()
        if filename in visited:
            continue
        visited.add(filename)
        modification_ids = _get_modification_ids(
            filename_modification_association[filename]
        )
        organism_id = _get_organism_id(metadata.organism)
        technology_id = _get_technology_id(metadata)
        try:
            with open(file_path) as fp:
                eufid = dataset_service.import_dataset(
                    fp,
                    source=file_path.as_posix(),
                    smid=smid,
                    title=title,
                    assembly_id=metadata.organism.assembly_id,
                    modification_ids=modification_ids,
                    organism_id=organism_id,
                    technology_id=technology_id,
                    annotation_source=annotation_source,
                )
            click.secho(
                f"Created dataset with EUFID: '{eufid}'.",
                fg="green",
            )
        except Exception as exc:
            click.secho(
                f"Failed to create dataset. {exc}... Skipping!",
                fg="red",
            )
            continue

    try:
        click.secho("Triggering charts update in the background ...", fg="green")
        _so_sunburst_update()
    except Exception as exc:
        click.secho(
            f"Failed to update charts. {exc}.",
            fg="red",
        )


def _so_sunburst_update():
    sunburst_service = get_sunburst_service()
    sunburst_service.trigger_background_update()


def _validate_input(uuid: str) -> ProjectTemplate:
    file_service = get_file_service()
    with file_service.open_project_request_file(uuid) as fh:
        project_template_raw = fh.read()
        project_template = ProjectTemplate.model_validate_json(project_template_raw)
    return project_template


def _get_modification_ids(values):
    modification_ids = []
    for rna, modomics in values:
        modification_id = (
            get_session()
            .execute(select(Modification.id).filter_by(rna=rna, modomics_id=modomics))
            .scalar_one()
        )
        modification_ids.append(modification_id)
    return modification_ids


def _get_organism_id(organism):
    return (
        get_session()
        .execute(
            select(Organism.id).filter_by(taxa_id=organism.taxa_id, cto=organism.cto)
        )
        .scalar_one()
    )


def _get_technology_id(metadata):
    return (
        get_session()
        .execute(
            select(DetectionTechnology.id).filter_by(
                method_id=metadata.method_id, tech=metadata.tech
            )
        )
        .scalar_one()
    )
