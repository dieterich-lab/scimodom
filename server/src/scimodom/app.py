from logging.config import dictConfig

import click
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import scoped_session

from scimodom.api.public import api
from scimodom.api.user import user_api
from scimodom.api.dataset import dataset_api
from scimodom.api.access import access_api
from scimodom.api.management import management_api
from scimodom.api.upload import upload_api
from scimodom.api.transfer import transfer_api
from scimodom.api.bam_file import bam_file_api
from scimodom.app_singleton import create_app_singleton
from scimodom.database.database import make_session, init
from scimodom.services.setup import get_setup_service
from scimodom.frontend import frontend
from scimodom.plugins.cli import (
    add_annotation,
    add_assembly,
    add_project,
    add_dataset,
    add_all,
    validate_dataset_title,
    upsert,
)
from scimodom.utils.url_routes import (
    API_PREFIX,
    USER_API_ROUTE,
    ACCESS_API_ROUTE,
    DATASET_API_ROUTE,
    UPLOAD_API_ROUTE,
    TRANSFER_API_ROUTE,
    DATA_MANAGEMENT_API_ROUTE,
    BAM_FILE_API_ROUTE,
)


def create_app():
    """Function factory to create Flask app."""

    app = create_app_singleton()
    CORS(app)
    # does not instantiate the class object...
    app.config.from_object("scimodom.config.Config")
    # since we haven't called app.logger there shouldn't be any default handlers...
    dictConfig(app.config["LOGGING"])

    engine, session = make_session(app.config["DATABASE_URI"])
    app.session = scoped_session(session)
    init(engine, lambda: app.session)
    setup_service = get_setup_service()
    setup_service.upsert_all()

    app.register_blueprint(api, url_prefix=f"/{API_PREFIX}")
    app.register_blueprint(user_api, url_prefix=USER_API_ROUTE)
    app.register_blueprint(access_api, url_prefix=ACCESS_API_ROUTE)
    app.register_blueprint(dataset_api, url_prefix=DATASET_API_ROUTE)
    app.register_blueprint(upload_api, url_prefix=UPLOAD_API_ROUTE)
    app.register_blueprint(transfer_api, url_prefix=TRANSFER_API_ROUTE)
    app.register_blueprint(management_api, url_prefix=DATA_MANAGEMENT_API_ROUTE)
    app.register_blueprint(bam_file_api, url_prefix=BAM_FILE_API_ROUTE)

    app.register_blueprint(frontend, url_prefix="/")

    jwt = JWTManager(app)

    @app.cli.command(
        "assembly", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.option(
        "--id",
        default=None,
        type=click.INT,
        help="Assembly ID. Download files for the current assembly (initial setup). This parameter, if given, overrides all other options.",
    )
    @click.option(
        "--name",
        default=None,
        type=click.STRING,
        help="Assembly name. Download files for any assembly. This option must be used with [--taxid].",
    )
    @click.option(
        "--taxid",
        default=None,
        type=click.INT,
        help="Taxonomy ID. Download files for any assembly. This option must be used with [--name].",
    )
    def assembly(id, name, taxid):
        """Prepare assembly."""
        if id:
            kwargs = {"assembly_id": id}
        else:
            if not name:
                raise NameError(
                    "Name [--name] is not defined. One of [--id] or [--name] and [--taxid] is required."
                )
            if taxid is None:
                raise NameError(
                    "Name [--taxid] is not defined. It is required with [--name]."
                )
            kwargs = {"assembly_name": name, "taxa_id": taxid}
        add_assembly(**kwargs)

    @app.cli.command(
        "annotation", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("id", type=click.INT)
    def annotation(id):
        """Prepare annotation.

        ID is the annotation_id (must already exists).
        """
        add_annotation(id)

    @app.cli.command(
        "project", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("template", type=click.Path(exists=True))
    def project(template):
        """Add a new project to the database.

        TEMPLATE is the path to a project template (json).
        """
        add_project(template)

    @app.cli.command(
        "dataset", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("smid", type=click.STRING)
    @click.argument("title", type=click.UNPROCESSED, callback=validate_dataset_title)
    @click.argument("filename", type=click.Path(exists=True))
    @click.option("--assembly", required=True, type=click.INT, help="Assembly ID.")
    @click.option(
        "-s",
        "--selection",
        default=[],
        multiple=True,
        type=click.INT,
        help="Selection ID(s). Repeat parameter to pass multiple selection IDs. This parameter, if given, overrides all other options.",
    )
    @click.option(
        "-m",
        "--modification",
        default=[],
        multiple=True,
        type=click.INT,
        help="Modification ID(s). Repeat parameter to pass multiple selection IDs. This option must be used with [--technology] and [--organism].",
    )
    @click.option(
        "-o",
        "--organism",
        default=None,
        type=click.INT,
        help="Organism ID. This option must be used with [--modification] and [--technology].",
    )
    @click.option(
        "-t",
        "--technology",
        default=None,
        type=click.INT,
        help="Technology ID. This option must be used with [--modification] and [--organism].",
    )
    def dataset(
        smid, title, filename, assembly, selection, modification, organism, technology
    ):
        """Add a new dataset to the database.

        \b
        SMID is the project ID to which this dataset is to be added.
        TITLE is the title of this dataset. String must be quoted.
        FILENAME is the path to the bedRMod (EU-formatted) file.
        """
        if selection:
            kwargs = {"selection_id": list(selection)}
        else:
            if not modification:
                raise NameError(
                    "Name [--modification] is not defined. One of [--selection] or [--modification] is required."
                )
            if technology is None:
                raise NameError(
                    "Name [--technology] is not defined. It is required with [--modification]."
                )
            if organism is None:
                raise NameError(
                    "Name [--organism] is not defined. It is required with [--modification]."
                )
            kwargs = {
                "modification_id": list(modification),
                "technology_id": technology,
                "organism_id": organism,
            }
        add_dataset(smid, title, filename, assembly, **kwargs)

    @app.cli.command(
        "batch", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("directory", type=click.Path(exists=True))
    @click.argument("templates", nargs=-1, type=click.STRING)
    def batch(directory, templates):
        """Add projects and dataset to the database
        in batch. All files must be under DIRECTORY.

        \b
        DIRECTORY is the path to templates and bedRMod (EU-formatted) files.
        TEMPLATES is the name (w/o extension) of one or more project templates.
        """
        add_all(directory, templates)

    @app.cli.command(
        "setup", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.option(
        "-m",
        "--model",
        default=None,
        type=click.STRING,
        help="""Upsert MODEL using [--table TABLE]. Performs an INSERT... ON DUPLICATE KEY UPDATE. Requires [--table TABLE]""",
    )
    @click.option(
        "-t",
        "--table",
        default=None,
        type=click.STRING,
        help="""Database table for MODEL with column names. Only columns matching __table__.columns are used. CSV format. Requires [--model MODEL]""",
    )
    @click.option(
        "--init",
        is_flag=True,
        help="This flag silently overrides other options. Called on application start-up.",
    )
    def setup(model, table, init):
        """Upsert selected or all default DB tables.
        Selected model/table names must exist.
        """
        kwargs = dict()
        if not init:
            if None not in (model, table):
                kwargs = {"model": model, "table": table}
            else:
                raise TypeError(
                    "'NoneType' object is not a valid argument for [--model] and/or [--table]."
                )
        upsert(init, **kwargs)

    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
