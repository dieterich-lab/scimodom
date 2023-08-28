__version_info__ = ("0", "0", "1")
__version__ = ".".join(__version_info__)


def create_app():
        
    import uuid
    
    from flask import Flask
    from flask_cors import CORS

    from sqlalchemy.orm import scoped_session
    from scimodom.database.database import engine, Session, init
    
    app = Flask(__name__)
    
    #app.secret_key = str(uuid.uuid4())
    app.config['SECRET_KEY'] = str(uuid.uuid4())
    app.config.from_object('scimodom.config.DevConfig')
    print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> {app.config}")
    app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    
    CORS(app)

    # app.config.from_object(config[config_mode])
    app.session = scoped_session(Session)
    init(engine, lambda: app.session)
    
    # does this goes here?
    @app.teardown_appcontext
    def cleanup(exception=None):
        app.session.remove()
    
    return app


#def create_app():
        
    #import uuid
    
    #from flask import Flask
    #from flask_cors import CORS
    
    #from sqlalchemy import create_engine
    #from sqlalchemy.orm import sessionmaker, scoped_session
    #from scimodom.database.database import init
    
    #app = Flask(__name__)
    
    ##app.secret_key = str(uuid.uuid4())
    #app.config['SECRET_KEY'] = str(uuid.uuid4())
    #app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)
    
    #CORS(app)
    
    ## hard coded here now - TODO: config/env
    #DATABASE = "mysql+mysqldb://eboileau:@localhost/scimodom"

    ## options -> pool_recycle, isolation_level
    ## connect_args={"check_same_thread": False}
    #engine = create_engine(DATABASE)

    #Session = sessionmaker(autocommit=False,
                           #autoflush=False,
                           #bind=engine)

    ## app.config.from_object(config[config_mode])
    #app.session = scoped_session(Session)
    #init(engine, lambda: app.session)
    
    ## does this goes here?
    #@app.teardown_appcontext
    #def cleanup(exception=None):
        #app.session.remove()
    
    #return app
