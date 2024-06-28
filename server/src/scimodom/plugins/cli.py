from collections import defaultdict
from pathlib import Path
import re

import click
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    Modification,
    DetectionTechnology,
    Organism,
)
from scimodom.services.annotation import AnnotationSource, get_annotation_service
from scimodom.services.dataset import get_dataset_service
from scimodom.services.project import get_project_service
from scimodom.services.assembly import (
    AssemblyVersionError,
    AssemblyNotFoundError,
    get_assembly_service,
)
from scimodom.services.permission import get_permission_service
from scimodom.services.setup import get_setup_service
from scimodom.services.user import get_user_service, NoSuchUser
import scimodom.utils.utils as utils
from scimodom.utils.project_dto import ProjectTemplate


def validate_dataset_title(ctx, param, value):
    """Validate parameter (str) length."""
    if len(value) > Dataset.title.type.length:
        raise click.BadParameter("Title cannot be longer than 255 characters!")
    return value


def add_assembly(**kwargs) -> None:
    """Provide a CLI function to manage assemblies.

    If "assembly_id" is given, prepare an assembly
    for the latest version, else add an alternative
    assembly using "taxa_id" and "name".
    """
    assembly_service = get_assembly_service()

    assembly_id = kwargs.get("assembly_id", None)
    if assembly_id:
        assembly = assembly_service.get_assembly_by_id(assembly_id)
        click.secho(
            f"Preparing assembly for {assembly.name}...",
            fg="green",
        )
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        try:
            assembly_service.prepare_assembly_for_version(assembly_id)
        except FileExistsError:
            click.secho(
                "Assembly directory exists... Aborting!",
                fg="red",
            )
            return
        except AssemblyVersionError:
            click.secho(
                "Cannot create assembly for this version... Aborting!",
                fg="red",
            )
            return
        click.secho("... done!", fg="green")
    else:
        assembly_name = kwargs["assembly_name"]
        taxa_id = kwargs["taxa_id"]
        click.secho(
            f"Adding alternative assembly for {assembly_name}...",
            fg="green",
        )
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        assembly_id = assembly_service.add_assembly(taxa_id, assembly_name)
        click.secho(f"... done! Assembly ID is {assembly_id}.", fg="green")


def add_annotation(taxa_id: int, source: AnnotationSource, **kwargs) -> None:
    """Provide a CLI function to manage annotation.

    Annotation must exists (only latest version allowed).

    :param taxa_id: Taxonomy ID.
    :type taxa_id: int
    :param source: Annotation source
    :type source: AnnotationSource
    """
    annotation_service = get_annotation_service()
    click.secho(
        f"Preparing {source.value} annotation for {taxa_id}...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    annotation_service.create_annotation(source, taxa_id, **kwargs)
    click.secho("... done!", fg="green")


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
            _add_assembly_to_template_if_none(metadata.organism, assembly_service)
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
        _ = project_service.get_by_id(smid)
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


def add_dataset(
    file_source: str,
    smid: str,
    title: str,
    assembly_id: int,
    modification_ids: list[int],
    organism_id: int,
    technology_id: int,
    annotation_source: AnnotationSource,
) -> None:
    """Provide a CLI function to add a new dataset.

    :param file_source: Dataset file.
    :type file_source: str
    :param smid: SMID (project must exists).
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
    """
    dataset_service = get_dataset_service()
    click.secho(
        f"Adding dataset '{title}' to project with SMID '{smid}'... ", fg="green"
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    try:
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
            )
    except Exception as exc:
        click.secho(f"Failed to create dataset: {exc}... Aborting!", fg="red")
        return
    click.secho(
        f"Created dataset with EUFID '{eufid}'...",
        fg="green",
    )
    click.secho("... done!", fg="green")


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
    file must be under 'input_directory'.

    :param directory: Directory where data files are located.
    :type directory: Path
    :param project_templates: A list of project templates
    :type templates: list of ProjectTemplate
    :param request_uuids: Original request UUIDs
    :type request_uuis: list of str
    :param annotation_source: Annotation source
    :type annotation_source: AnnotationSource
    """
    regexp = re.compile(r"(file=)(.*)(?:,\s*)(title=)(.*)")
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
                _add_assembly_to_template_if_none(metadata.organism, assembly_service)
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
    click.secho("... done!", fg="green")


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
            click.secho("The option '--table <name>' is required.", fg="red")
            exit(1)
        valid_names = setup_service.get_valid_import_file_names()
        if file_name not in valid_names:
            v = ", ".join(valid_names)
            click.secho(
                f"The option '--table <name>' needs a valid name ({v}).", fg="red"
            )
            exit(1)

        click.secho(setup_service.get_upsert_message(file_name), fg="green")
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        setup_service.upsert_one(file_name)
    click.secho("Successfully performed INSERT... ON DUPLICATE KEY UPDATE.", fg="green")


def _add_assembly_to_template_if_none(organism, assembly_service):
    click.secho("Checking if assembly ID is defined...", fg="green")
    if organism.assembly_id is None:
        assembly_id = assembly_service.add_assembly(
            organism.taxa_id, organism.assembly_name
        )
        click.secho(
            f"Updating project metadata template with assembly ID '{assembly_id}'... ",
            fg="yellow",
        )
        organism.assembly_id = assembly_id
    else:
        _ = assembly_service.get_assembly_by_id(organism.assembly_id)


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
