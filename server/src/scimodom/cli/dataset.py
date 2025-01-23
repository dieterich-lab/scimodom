from collections import defaultdict
from pathlib import Path
import re

import click
from sqlalchemy import select

from scimodom.database.database import get_session
from scimodom.database.models import (
    DetectionTechnology,
    Organism,
    Modification,
)
from scimodom.cli.utilities import (
    add_assembly_to_template_if_none,
)

from scimodom.services.assembly import AssemblyNotFoundError, get_assembly_service
from scimodom.services.dataset import get_dataset_service
from scimodom.services.project import get_project_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.utils.dtos.project import (
    ProjectTemplate,
)
from scimodom.utils.specs.enums import AnnotationSource


def add_dataset(
    file_source: str,
    smid: str,
    title: str,
    assembly_id: int,
    modification_ids: list[int],
    organism_id: int,
    technology_id: int,
    annotation_source: AnnotationSource,
    dry_run_flag: bool = False,
    eufid: str | None = None,
) -> None:
    """Provide a CLI function to add a new dataset or update
    data and annotation records an existing dataset.

    :param file_source: Dataset file.
    :type file_source: str
    :param smid: SMID (project must exist).
    :type smid: str
    :param title: Dataset title
    :type title: str
    :param assembly_id: Assembly ID
    :type assembly_id: int
    :param modification_ids: Modification ID(s) (RNA type, modomics ID)
    :type modification_ids: list of int
    :param technology_id: Technology ID (method ID, technology)
    :type technology_id: int
    :param organism_id: Organism ID (taxa ID, cto)
    :type organism_id: int
    :param annotation_source: Annotation source
    :type annotation_source: AnnotationSource
    :param dry_run_flag: Dry run flag. Default is False.
    :type dry_run_flag: bool, optional
    :param eufid: EUFID ID for which to update data and data annotation records. Default is None.
    :type eufid: str, optional
    """
    dataset_service = get_dataset_service()

    colour = "green"
    msg = f"Adding dataset '{title}' to project with SMID '{smid}'... "
    if dry_run_flag:
        msg = f"DRY RUN: {msg}"
        colour = "yellow"
    elif eufid is not None:
        msg = f"Updating data records for dataset '{eufid}'..."
    click.secho(msg, fg=colour)
    click.secho("Continue [y/n]?", fg=colour)
    c = click.getchar()
    if c not in ["y", "Y"]:
        return

    try:
        click.secho("Created or updated dataset ...", fg=colour)
        with open(file_source) as fp:
            eufid = dataset_service.import_dataset(
                fp,
                source=file_source,
                smid=smid,
                title=title,
                assembly_id=assembly_id,
                modification_ids=modification_ids,
                organism_id=organism_id,
                technology_id=technology_id,
                annotation_source=annotation_source,
                dry_run_flag=dry_run_flag,
                eufid=eufid,
            )
        click.secho(f"    ... done (EUFID '{eufid}').", fg=colour)
    except Exception as exc:
        click.secho("    ... FAILED!", fg="red")
        click.secho(f"Failed to create or update dataset: {exc}... Aborting!", fg="red")
        return
    _so_sunburst_update()


def _so_sunburst_update():
    click.secho("Triggering sunburst update in the background ...", fg="green")
    sunburst_service = get_sunburst_service()
    sunburst_service.trigger_background_update()


def add_all(
    input_directory: Path,
    project_templates: list[ProjectTemplate],
    request_uuids: list[str],
    annotation_source: AnnotationSource,
) -> None:
    """Provide a CLI function to batch add projects and dataset.

    The "note" from the metadata template must contain the
    dataset file name and title as follows:
    'file=filename.bedrmod, title=title'. All dataset
    files must be under 'input_directory'. All datasets must
    be annotated using the same annotation source.

    :param input_directory: Directory where data files are located.
    :type input_directory: Path
    :param project_templates: A list of project templates - templates
    must be located under the application project_requests directory.
    :type project_templates: list of ProjectTemplate
    :param request_uuids: Original request UUIDs
    :type request_uuids: list[str]
    :param annotation_source: Annotation source
    :type annotation_source: AnnotationSource
    """
    regexp = re.compile(r"(file=)(.*),\s*(title=)(.*)")
    project_service = get_project_service()
    dataset_service = get_dataset_service()
    assembly_service = get_assembly_service()

    valid_templates = {}
    for project_template, request_uuid in zip(project_templates, request_uuids):
        valid_metadata = []
        valid_filenames = defaultdict(list)
        for metadata in project_template.metadata:
            filename = regexp.search(metadata.note).group(2).strip()
            try:
                add_assembly_to_template_if_none(metadata.organism, assembly_service)
                valid_metadata.append(metadata)
                valid_filenames[filename].append((metadata.rna, metadata.modomics_id))
            except AssemblyNotFoundError:
                click.secho(
                    f"No such assembly '{metadata.organism.assembly_id}'... skipping '{filename}'!",
                    fg="red",
                )
                continue
        project_template.metadata = valid_metadata
        if len(valid_metadata) == 0:
            click.secho(
                f"No valid dataset... skipping '{project_template.title}'!",
                fg="red",
            )
            continue
        click.secho(f"Adding project {project_template.title}...", fg="green")
        try:
            smid = project_service.create_project(project_template, request_uuid)
            click.secho(
                f"Created project with SMID '{smid}'... done!",
                fg="green",
            )
            valid_templates[smid] = (project_template, valid_filenames)
        except Exception as exc:
            click.secho(
                f"Failed to create project: {exc}... skipping {project_template.title}!",
                fg="red",
            )
            continue

    visited = set()
    for smid, (project, filenames) in valid_templates.items():
        for metadata in project.metadata:
            filename = regexp.search(metadata.note).group(2).strip()
            file_path = Path(input_directory, filename)
            title = regexp.search(metadata.note).group(4).strip()
            if filename in visited:
                continue
            visited.add(filename)
            modification_ids = _get_modification_ids(filenames[filename])
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
                    f"Created dataset with EUFID '{eufid}' for project with SMID '{smid}'...",
                    fg="green",
                )
            except Exception as exc:
                click.secho(
                    f"Failed to create dataset: {exc}... skipping {filename}!", fg="red"
                )
                continue
    _so_sunburst_update()
    click.secho("... done!", fg="green")


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
