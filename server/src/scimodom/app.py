from scimodom.app_singleton import create_app_singleton


def create_app():
    """Function factory to create Flask app."""
    from logging.config import dictConfig
    from flask_cors import CORS

    from sqlalchemy.orm import scoped_session
    from scimodom.database.database import make_session, init

    app = create_app_singleton()
    CORS(app)
    # does not instantiate the class object...
    app.config.from_object("scimodom.config.Config")
    # since we haven't called app.logger there shouldn't be any default handlers...
    dictConfig(app.config["LOGGING"])

    engine, session = make_session(app.config["DATABASE_URI"])
    app.session = scoped_session(session)
    init(engine, lambda: app.session)

    from scimodom.frontend import frontend
    from scimodom.api import api

    app.register_blueprint(frontend, url_prefix="/")
    app.register_blueprint(api, url_prefix="/api/v0")

    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()

    return app
