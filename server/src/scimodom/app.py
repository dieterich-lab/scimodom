from logging.config import dictConfig

import click
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import scoped_session

from scimodom.app_singleton import create_app_singleton
from scimodom.config import set_config_from_environment, get_config
from scimodom.database.database import make_session, init

from scimodom.cli.annotation import add_annotation
from scimodom.cli.utilities import upsert
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
from scimodom.utils.specs.enums import AnnotationSource


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

    # API
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

    # CLI
    from scimodom.cli.assembly import assembly_cli
    from scimodom.cli.selection import selection_cli
    from scimodom.cli.project import project_cli
    from scimodom.cli.dataset import dataset_cli
    from scimodom.cli.charts import charts_cli

    app.register_blueprint(assembly_cli)
    app.register_blueprint(selection_cli)
    app.register_blueprint(project_cli)
    app.register_blueprint(dataset_cli)
    app.register_blueprint(charts_cli)

    jwt = JWTManager(app)

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

    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
