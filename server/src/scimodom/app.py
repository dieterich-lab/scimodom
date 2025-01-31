from logging.config import dictConfig

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy.orm import scoped_session

from scimodom.app_singleton import create_app_singleton
from scimodom.config import set_config_from_environment, get_config
from scimodom.database.database import make_session, init

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


def create_app():
    """Provide a function factory to create app."""
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
    from scimodom.cli.annotation import annotation_cli
    from scimodom.cli.selection import selection_cli
    from scimodom.cli.project import project_cli
    from scimodom.cli.dataset import dataset_cli
    from scimodom.cli.charts import charts_cli

    app.register_blueprint(assembly_cli)
    app.register_blueprint(annotation_cli)
    app.register_blueprint(selection_cli)
    app.register_blueprint(project_cli)
    app.register_blueprint(dataset_cli)
    app.register_blueprint(charts_cli)

    jwt = JWTManager(app)

    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
