from logging.config import dictConfig

import click
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import scoped_session

from scimodom.app_singleton import create_app_singleton
from scimodom.config import set_config_from_environment, get_config
from scimodom.database.database import make_session, init
from scimodom.plugins.cli import (
    add_annotation,
    add_assembly,
    add_project,
    add_user_to_project,
    add_dataset,
    add_all,
    validate_dataset_title,
    upsert,
)
from scimodom.services.annotation import AnnotationSource
from scimodom.services.file import get_file_service
from scimodom.services.setup import get_setup_service
from scimodom.services.url import (
    API_PREFIX,
    BAM_FILE_API_ROUTE,
    DATA_MANAGEMENT_API_ROUTE,
    DATASET_API_ROUTE,
    MODIFICATION_API_ROUTE,
    PROJECT_API_ROUTE,
    TRANSFER_API_ROUTE,
    USER_API_ROUTE,
)
from scimodom.utils.project_dto import ProjectTemplate


def create_app():
    """Function factory to create Flask app."""

    app = create_app_singleton()
    CORS(app)
    set_config_from_environment()
    app.config.from_object(get_config())
    dictConfig(app.config["LOGGING"])

    engine, session = make_session(app.config["DATABASE_URI"])
    app.session = scoped_session(session)
    init(engine, lambda: app.session)
    setup_service = get_setup_service()
    setup_service.upsert_all()

    from scimodom.frontend import frontend
    from scimodom.api.utilities import api
    from scimodom.api.bam_file import bam_file_api
    from scimodom.api.dataset import dataset_api
    from scimodom.api.management import management_api
    from scimodom.api.modification import modification_api
    from scimodom.api.project import project_api
    from scimodom.api.transfer import transfer_api
    from scimodom.api.user import user_api

    app.register_blueprint(frontend, url_prefix="/")
    app.register_blueprint(api, url_prefix=f"/{API_PREFIX}")
    app.register_blueprint(bam_file_api, url_prefix=BAM_FILE_API_ROUTE)
    app.register_blueprint(dataset_api, url_prefix=DATASET_API_ROUTE)
    app.register_blueprint(management_api, url_prefix=DATA_MANAGEMENT_API_ROUTE)
    app.register_blueprint(modification_api, url_prefix=MODIFICATION_API_ROUTE)
    app.register_blueprint(project_api, url_prefix=PROJECT_API_ROUTE)
    app.register_blueprint(transfer_api, url_prefix=TRANSFER_API_ROUTE)
    app.register_blueprint(user_api, url_prefix=USER_API_ROUTE)

    jwt = JWTManager(app)

    @app.cli.command(
        "assembly", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.option(
        "--id",
        default=None,
        type=click.INT,
        help="Assembly ID. Prepare a new assembly for the latest version. Assembly must exists. This parameter overrides all other options.",
    )
    @click.option(
        "--name",
        default=None,
        type=click.STRING,
        help="Assembly name. Add an alternative assembly to the database. This option must be used with [--taxid].",
    )
    @click.option(
        "--taxid",
        default=None,
        type=click.INT,
        help="Taxonomy ID. Add an alternative assembly to the database. This option must be used with [--name].",
    )
    def assembly(id, name, taxid):
        """Prepare new assembly or add alternative assembly."""
        if id:
            kwargs = {"assembly_id": id}
        else:
            if not name:
                raise NameError(
                    "Name [--name] is not defined. It is required with [--taxid]."
                )
            if not taxid:
                raise NameError(
                    "Name [--taxid] is not defined. It is required with [--name]."
                )
            kwargs = {"assembly_name": name, "taxa_id": taxid}
        add_assembly(**kwargs)

    @app.cli.command(
        "annotation", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("taxid", type=click.INT)
    @click.option(
        "--source",
        required=True,
        type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
        help="Annotation source.",
    )
    @click.option(
        "--domain",
        default=None,
        type=click.STRING,
        help="Taxonomic domain for gtdbrna. This option must be used with [--name].",
    )
    @click.option(
        "--name",
        default=None,
        type=click.STRING,
        help="GtRNAdb species name. This option must be used with [--domain].",
    )
    def annotation(taxid, source, domain, name):
        """Prepare annotation.

        TAXA ID is the taxa_id.
        """
        kwargs = {}
        annotation_source = AnnotationSource(source)
        if annotation_source == AnnotationSource.GTRNADB:
            if not domain:
                raise NameError(
                    "Name [--domain] is not defined. It is required with [--name]."
                )
            if not name:
                raise NameError(
                    "Name [--name] is not defined. It is required with [--domain]."
                )
            kwargs = {"domain": domain, "name": name}
        add_annotation(taxid, annotation_source, **kwargs)

    @app.cli.command(
        "project", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("request_uuid", type=click.STRING)
    @click.option(
        "--skip-add-user",
        is_flag=True,
        show_default=True,
        default=False,
        help="Do not add user to project.",
    )
    def project(request_uuid, skip_add_user):
        """Add a new project to the database.

        REQUEST_UUID is the UUID of a project request.
        """
        add_user = not skip_add_user
        file_service = get_file_service()
        with file_service.open_project_request_file(request_uuid) as fh:
            project_template_raw = fh.read()
        project_template = ProjectTemplate.model_validate_json(project_template_raw)
        add_project(project_template, request_uuid, add_user=add_user)

    @app.cli.command(
        "permission", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("username", type=click.STRING)
    @click.argument("smid", type=click.STRING)
    def permission(username, smid):
        """Force add a user to a project.

        \b
        USERNAME is the user email.
        SMID is the project ID to which this user is to be associated.
        """
        add_user_to_project(username, smid)

    @app.cli.command(
        "dataset", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("filename", type=click.Path(exists=True))
    @click.argument("smid", type=click.STRING)
    @click.argument("title", type=click.UNPROCESSED, callback=validate_dataset_title)
    @click.option("--assembly", required=True, type=click.INT, help="Assembly ID.")
    @click.option(
        "--annotation",
        required=True,
        type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
        help="Annotation source.",
    )
    @click.option(
        "-m",
        "--modification",
        default=[],
        multiple=True,
        required=True,
        type=click.INT,
        help="Modification ID(s). Repeat parameter to pass multiple selection IDs.",
    )
    @click.option(
        "-o",
        "--organism",
        default=None,
        required=True,
        type=click.INT,
        help="Organism ID.",
    )
    @click.option(
        "-t",
        "--technology",
        default=None,
        required=True,
        type=click.INT,
        help="Technology ID.",
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
        help="Update data and data annotation records for existing dataset with the supplied EUFID instead of creating a new one.",
    )
    def dataset(
        filename,
        smid,
        title,
        assembly,
        annotation,
        modification,
        organism,
        technology,
        dry_run,
        eufid,
    ):
        """Add a new dataset to the database or update records for an existing dataset.

        \b
        FILENAME is the path to the bedRMod (EU-formatted) file.
        SMID is the project ID to which this dataset is to be added.
        TITLE is the title of this dataset. String must be quoted.
        """
        annotation_source = AnnotationSource(annotation)
        add_dataset(
            filename,
            smid,
            title,
            assembly,
            list(modification),
            organism,
            technology,
            annotation_source,
            dry_run_flag=dry_run,
            eufid=eufid,
        )

    @app.cli.command(
        "batch", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("input_directory", type=click.Path(exists=True))
    @click.argument("request_uuids", nargs=-1, type=click.STRING)
    @click.option(
        "--annotation",
        required=True,
        type=click.Choice(["ensembl", "gtrnadb"], case_sensitive=False),
        help="Annotation source.",
    )
    def batch(input_directory, request_uuids, annotation):
        """Add projects and dataset in batch.
        All dataset files must be under INPUT_DIRECTORY.
        Implicitely assumed that all have the same annotation
        source. There is no [--dry-run] option. This method cannot
        be used to update records for existing datasets.

        \b
        INPUT_DIRECTORY is the path to bedRMod (EU-formatted) files.
        REQUEST_UUIDS is the name (w/o extension) of one or more project templates.
        """
        annotation_source = AnnotationSource(annotation)
        file_service = get_file_service()
        project_template_list = []
        for uuid in request_uuids:
            with file_service.open_project_request_file(uuid) as fh:
                project_template_raw = fh.read()
            project_template = ProjectTemplate.model_validate_json(project_template_raw)
            project_template_list.append(project_template)
        add_all(
            input_directory, project_template_list, request_uuids, annotation_source
        )

    @app.cli.command(
        "setup", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.option(
        "-t",
        "--table",
        default=None,
        type=click.STRING,
        help="Name of the CSV file to use, e.g. ncbi_taxa.csv. The database table to load will be determined by that.",
    )
    @click.option(
        "--init",
        is_flag=True,
        help="This flag silently overrides other options. Called on application start-up.",
    )
    def setup(table, init):
        """Upsert selected or all default DB tables.
        Selected model/table names must exist.
        """
        kwargs = dict()
        if not init:
            kwargs = {"table": table}
        upsert(init, **kwargs)

    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
