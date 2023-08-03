from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import DeclarativeBase
    
# ???
DATABASE = "mysql+mysqldb://eboileau:@localhost/classicmodels"

# options -> pool_recycle, isolation_level
engine = create_engine(DATABASE)

# scoped_session -> we don’t have to care about threads
# sQLAlchemy checks to see if a thread-local session exists, if it does, it uses it, otherwise it creates one first.
# options
Session = scoped_session(sessionmaker(autocommit=False,
                                      autoflush=False,
                                      bind=engine))
                                         
class Base(DeclarativeBase):
    pass
    #query = Session.query_property()
    
class Reflected(DeferredReflection):
    __abstract__ = True
    
Base.query = Session.query_property()

def init():
    
    from . import models
    Reflected.prepare(engine)

# do we need a @click.command('init-db'), see e.g. https://flask.palletsprojects.com/en/2.3.x/tutorial/database/#create-the-tables
# dev vs. production



------------------------------------------------

from sqlalchemy.orm import DeclarativeBase




# declarative base class
class Base(DeclarativeBase):
    pass
