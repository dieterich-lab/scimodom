from collections import defaultdict
import json
from pathlib import Path
import sys
import traceback

import click
from sqlalchemy import select

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.database.models import (
    Project,
    Dataset,
    Modification,
    DetectionTechnology,
    Organism,
    Assembly,
)
import scimodom.database.queries as queries
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.project import get_project_service
from scimodom.services.dataset import DataService
from scimodom.services.setup import get_setup_service
from scimodom.services.user import get_user_service, NoSuchUser
import scimodom.utils.utils as utils


def validate_dataset_title(ctx, param, value):
    """Validate parameter (str) length."""
    if len(value) > Dataset.title.type.length:
        raise click.BadParameter("Title cannot be longer than 255 characters!")
    return value


def add_assembly(**kwargs) -> None:
    """Provides a CLI function to set up a new assembly.
    This function does not add a new assembly to the database,
    but merely creates the data structure.

    :param assembly_id: Assembly ID, must exists.
    :type assembly_id: int
    :param assembly_name: Assembly name, must exists.
    :type assembly_name: str
    :param taxa_id: Taxonomy ID, must exists.
    :type taxa_id: int
    """
    session = get_session()

    assembly_id = kwargs.get("assembly_id", None)
    if assembly_id is not None:
        service = AssemblyService.from_id(session, assembly_id=assembly_id)
    else:
        click.secho("Checking if assembly exists...", fg="green")
        assembly_name = kwargs["assembly_name"]
        taxa_id = kwargs["taxa_id"]
        service = AssemblyService.from_new(session, name=assembly_name, taxa_id=taxa_id)
        if service._is_new:
            parent, filen = service.get_chain_path()
            chain_file = Path(parent, filen)
            click.secho(f"Done downloading chain file {chain_file}.", fg="green")
        else:
            click.secho("Assembly already exists... nothing to do.", fg="green")
        return

    click.secho(
        f"Preparing assembly for {service._name} ({service._taxid}) to {Config.DATABASE_URI}...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    service.create_new()
    click.secho("Successfully created.", fg="green")
    session.close()


def add_annotation(annotation_id: int) -> None:
    """Provides a CLI function to set up a new annotation.
    This function does not add a new annotation to the database,
    but merely creates the data structure.

    :param annotation_id: Annotation ID, must exists.
    :type annotation_id: int
    """
    session = get_session()
    service = AnnotationService(session, annotation_id=annotation_id)
    click.secho(
        f"Preparing annotation for {service._taxid} ({service._release}) to {Config.DATABASE_URI}...",
        fg="green",
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    service.create_annotation()
    click.secho("Successfully created.", fg="green")
    session.close()


def add_project(project_template: str | Path, add_user: bool = True) -> None:
    """Provides a CLI function to add a new project.

    :param project_template: Path to a json file with
    require fields.
    :type project_template: str or Path
    :param add_user: Associate user and newly created project
    :type add_user: bool
    """
    # load project metadata
    project = json.load(open(project_template))
    # add project
    click.secho(
        f"Adding project {project_template} to {Config.DATABASE_URI}...", fg="green"
    )
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    project_service = get_project_service()
    project_service.create_project(project)
    click.secho(
        f"Successfully created. The SMID for this project is {project_service.get_smid()}.",
        fg="green",
    )
    if add_user:
        username = project["contact_email"]
        click.secho(f"Adding user {username} to newly created project...", fg="green")
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        user_service = get_user_service()
        try:
            user = user_service.get_user_by_email(username)
        except NoSuchUser:
            click.secho(
                f"Unknown user {username}... Aborting!",
                fg="red",
            )
        else:
            project_service.associate_project_to_user(user)
            click.secho(
                "Successfully added user to project.",
                fg="green",
            )


def add_user_to_project(username: str, smid: str) -> None:
    """Provides a CLI function to force add a user to a project.

    :param username: Username (email)
    :type username: str
    :param smid: SMID
    :type smid: str
    """
    session = get_session()
    click.secho(f"Adding user {username} to {smid}...", fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    project_service = get_project_service()
    user_service = get_user_service()
    try:
        user = user_service.get_user_by_email(username)
    except NoSuchUser:
        click.secho(
            f"Unknown user {username}... Aborting!",
            fg="red",
        )
    else:
        query = select(Project.id)
        smids = session.execute(query).scalars().all()
        if smid not in smids:
            click.secho(
                f"Unrecognised SMID {smid}... Aborting!",
                fg="red",
            )
            return
        project_service.associate_project_to_user(user, smid=smid)
        click.secho(
            "Successfully added user to project.",
            fg="green",
        )


def add_dataset(
    smid: str, title: str, filen: str | Path, assembly_id: int, **kwargs
) -> None:
    """Provides a CLI function to add a new dataset
    to a project. Parameter values are validated by
    DataService. Project and assembly must exist.

    :param smid: SMID (project must exists).
    :type smid: str
    :param title: Dataset title
    :type title: str
    :param filen: Path to dataset
    :type filen: str or Path
    :param assembly_id: Assembly ID
    :type assembly_id: int
    :param selection_id: Selection ID(s)
    :type selection_id: int or list of int
    :param modification_id: Modification ID(s) (RNA type, modomics ID)
    :type modification_id: int or list of int
    :param technology_id: Technology ID (method ID, technology)
    :type technology_id: int
    :param organism_id: Organism ID (taxa ID, cto)
    :type organism_id: int
    """
    session = get_session()

    selection_id = kwargs.get("selection_id", None)
    if selection_id is not None:
        service = DataService.from_selection(
            session, smid, title, filen, assembly_id, selection_id=selection_id
        )
    else:
        modification_id = kwargs["modification_id"]
        technology_id = kwargs["technology_id"]
        organism_id = kwargs["organism_id"]
        service = DataService.from_new(
            session,
            smid,
            title,
            filen,
            assembly_id,
            modification_id=modification_id,
            technology_id=technology_id,
            organism_id=organism_id,
        )
    msg = f"Adding dataset {service._filen} to project with SMID={service._smid} for assembly ID={service._assembly_id}, with modification IDs={', '.join([str(m) for m in service._modification_id])}, technology ID={service._technology_id}, and organism ID={service._organism_id} to {Config.DATABASE_URI}..."
    click.secho(msg, fg="green")
    click.secho("Continue [y/n]?", fg="green")
    c = click.getchar()
    if c not in ["y", "Y"]:
        return
    service.create_dataset()
    click.secho(
        f"Successfully created. The EUFID for this dataset is {service.get_eufid()}.",
        fg="green",
    )
    session.close()


def add_all(directory: Path, templates: list[str]) -> None:
    """Provides a CLI function to add one or more
    projects and the associated dataset in batch (no
    prompt confirmation). This requires a non-standard
    project template (json) with additional keys:
    "file_name" and "data_title" for each "metadata" value.
    All templates and bedRMod (EU-formatted) files must
    be under the same directory. Values in the template
    are used "as is" to query the database.

    :param directory: Directory where project templates and data
    files are located.
    :type directory: Path
    :param templates: A list of project templates (file name only w/o extension)
    :type templates: list of str
    """
    extra_cols = {"file": "file_name", "title": "data_title"}

    session = get_session()

    projects = _get_projects(directory, templates, list(extra_cols.values()))

    for project in projects:
        project_file = project["path"]
        project_title = project["title"]
        click.secho(f"Adding {project_title}...", fg="green")
        try:
            project_service = get_project_service()
            project_service.create_project(project)
            smid = project_service.get_smid()
            metadata = _get_dataset(project, extra_cols["file"])
            for filen, meta in metadata.items():
                data_file = Path(directory, filen)
                if not data_file.is_file():
                    click.secho(
                        f"FileNotFoundError: not such file {data_file.as_posix()}...",
                        fg="red",
                    )
                    raise FileNotFoundError
                if len(meta) > 1:
                    try:
                        (
                            rna_type,
                            modomics_id,
                            method_id,
                            technology,
                            taxa_id,
                            cto,
                            assembly,
                            title,
                        ) = _get_repeated(meta, extra_cols["title"])
                    except TypeError:
                        click.secho(
                            f"There is a problem with the template for dataset {filen}...",
                            fg="red",
                        )
                        raise
                else:
                    (
                        rna_type,
                        modomics_id,
                        method_id,
                        technology,
                        taxa_id,
                        cto,
                        assembly,
                        title,
                    ) = _get_single(meta[0], extra_cols["title"])
                # query selection
                # catch all SQLAlchemy exceptions/database integrity errors...
                modification_ids = []
                for mid in modomics_id:
                    query = queries.query_column_where(
                        Modification,
                        "id",
                        filters={"modomics_id": mid, "rna": rna_type},
                    )
                    modification_ids.append(session.execute(query).scalar_one())
                query = queries.query_column_where(
                    DetectionTechnology,
                    "id",
                    filters={"method_id": method_id, "tech": technology},
                )
                technology_id = session.execute(query).scalar_one()
                query = queries.query_column_where(
                    Organism,
                    "id",
                    filters={"taxa_id": taxa_id, "cto": cto},
                )
                organism_id = session.execute(query).scalar_one()
                # any "new" assembly is created above on create_project()
                query = queries.query_column_where(
                    Assembly,
                    "id",
                    filters={"name": assembly, "taxa_id": taxa_id},
                )
                assembly_id = session.execute(query).scalar_one()
                # add dataset to project
                data_service = DataService.from_new(
                    session,
                    smid,
                    title,
                    Path(directory, filen),
                    assembly_id,
                    modification_id=modification_ids,
                    technology_id=technology_id,
                    organism_id=organism_id,
                )
                data_service.create_dataset()
                click.secho(
                    f"Successfully created. The EUFID for this dataset is {data_service.get_eufid()}.",
                    fg="green",
                )
        except Exception as exc:
            msg = f"Failed to add project template {project_file}: {exc}. Skipping project alltogether!"
            click.secho(msg, fg="red")
            traceback.print_exc(file=sys.stdout)
            session.rollback()
        else:
            click.secho(
                f"Successfully created. The SMID for this project is {smid}.",
                fg="green",
            )
        finally:
            session.close()


def upsert(init: bool, **kwargs) -> None:
    """Provies a CLI function for the SetupService.
    Upsert a given table, or all default tables (defined
    in the config).

    :param init: Upsert all default tables (same as start-up)
    :type init: bool
    """
    setup_service = get_setup_service()
    if init:
        setup_service.upsert_all()
    else:
        model = utils.get_model(kwargs.get("model"))
        table = setup_service.get_table(model, kwargs.get("table"))
        setup_service.validate_table(model, table)
        msg = (
            f"Updating {model.__name__} (table {model.__table__.name}) using "
            f"the following columns: {table.columns.tolist()}."
        )
        click.secho(msg, fg="green")
        click.secho("Continue [y/n]?", fg="green")
        c = click.getchar()
        if c not in ["y", "Y"]:
            return
        setup_service.bulk_upsert(model, table)
    click.secho("Successfully performed INSERT... ON DUPLICATE KEY UPDATE.", fg="green")


def _get_single(metadata, title):
    return (
        metadata["rna"],
        [metadata["modomics_id"]],
        metadata["method_id"],
        metadata["tech"],
        int(metadata["organism"]["taxa_id"]),
        metadata["organism"]["cto"],
        metadata["organism"]["assembly"],
        metadata[title],
    )


def _get_repeated(metadata, title):
    for key in ["rna", "tech", "method_id"]:
        if len(set([m[key] for m in metadata])) > 1:
            click.secho(f"Only one {key} type allowed per dataset!", fg="red")
            return None
    for key in ["taxa_id", "cto", "assembly"]:
        if len(set([m["organism"][key] for m in metadata])) > 1:
            click.secho(
                f"Only one {key} type allowed per dataset for organism!", fg="red"
            )
            return None
    if len(set([m[title] for m in metadata])) > 1:
        click.secho("Titles differ!", fg="red")
        return None
    modomics_id = [m["modomics_id"] for m in metadata]
    if len(set(modomics_id)) == 1:
        click.secho("Multiple metadata entries appear to be identical!", fg="red")
        return None
    return (
        metadata[0]["rna"],
        modomics_id,
        metadata[0]["method_id"],
        metadata[0]["tech"],
        int(metadata[0]["organism"]["taxa_id"]),
        metadata[0]["organism"]["cto"],
        metadata[0]["organism"]["assembly"],
        metadata[0][title],
    )


def _get_templates(directory, templates):
    all_paths = []
    for template in templates:
        path = Path(directory, f"{template}.json")
        if not path.is_file():
            click.secho(f"Template {path} missing... Skipping!", fg="red")
            continue
        all_paths.append(path)
    return all_paths


def _get_projects(directory, templates, extra_cols):
    all_templates = _get_templates(directory, templates)
    all_projects = []
    for template in all_templates:
        handle = open(template, "r")
        project = json.load(handle)
        project["path"] = template.as_posix()
        for d in utils.to_list(project["metadata"]):
            try:
                utils.check_keys_exist(d.keys(), extra_cols)
            except:
                click.secho(
                    f"Missing keys in {template} for metadata. Skipping project alltogether!",
                    fg="red",
                )
                break
        else:
            all_projects.append(project)
        handle.close()
    return all_projects


def _get_dataset(project, filen):
    d = defaultdict(list)
    for metadata in project["metadata"]:
        d[metadata[filen]].append(metadata)
    return d
