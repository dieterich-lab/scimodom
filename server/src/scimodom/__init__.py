__version_info__ = ("0", "0", "1")
__version__ = ".".join(__version_info__)


def create_app():
    """Function factory to create Flask app."""
    import uuid
    from logging.config import dictConfig

    from flask import Flask
    from flask_cors import CORS

    from sqlalchemy.orm import scoped_session
    from scimodom.database.database import make_session, init

    from scimodom.services.setup import SetupService

    app = Flask("scimodom")
    CORS(app)
    # does not instantiate the class object...
    app.config.from_object("scimodom.config.Config")
    # since we haven't called app.logger there shouldn't be any default handlers...
    dictConfig(app.config["LOGGING"])

    print(f" * Local environment: {'on' if app.config['LOCAL_APP'] else 'off'}")

    engine, session = make_session(app.config["DATABASE_URI"])
    app.session = scoped_session(session)
    init(engine, lambda: app.session)

    setup = SetupService(app.session)
    setup.upsert_all()

    from .api import api

    app.register_blueprint(api, url_prefix="/api/v0")

    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
