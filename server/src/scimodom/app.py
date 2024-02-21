from logging.config import dictConfig

import click
from flask_cors import CORS
from sqlalchemy.orm import scoped_session

from scimodom.api import api
from scimodom.app_singleton import create_app_singleton
from scimodom.database.database import make_session, init
from scimodom.frontend import frontend
from scimodom.plugins.cli import add_project


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

    app.register_blueprint(api, url_prefix="/api/v0")
    app.register_blueprint(frontend, url_prefix="/")

    @app.cli.command(
        "project", epilog="Check docs at https://dieterich-lab.github.io/scimodom/."
    )
    @click.argument("template", type=click.Path(exists=True))
    def project(template):
        """Add a new project to the database.

        TEMPLATE is the path to a project template (json).
        """
        add_project(template)

    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
