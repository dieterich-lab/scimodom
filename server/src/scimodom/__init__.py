__version_info__ = ("0", "0", "1")
__version__ = ".".join(__version_info__)


def create_app():
        
    import uuid
    
    from flask import Flask
    from flask_cors import CORS

    from sqlalchemy.orm import scoped_session
    from scimodom.database.database import Session, init
    
    app = Flask(__name__)
    
    #app.secret_key = str(uuid.uuid4())
    app.config['SECRET_KEY'] = str(uuid.uuid4())
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    
    CORS(app)

    # app.config.from_object(config[config_mode])
    app.session = scoped_session(Session)
    init(lambda: app.session)
    
    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()
    
    return app
