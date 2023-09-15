from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


_engine = None
_session = None


# hard coded here now - TODO: config from env here <---
DATABASE_URI = "mysql+mysqldb://eboileau:@localhost/scimodom"

# options -> pool_recycle, isolation_level
# connect_args={"check_same_thread": False}
engine = create_engine(DATABASE_URI)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_session():
    if _session is None:
        raise Exception("Session not initialized!")
    else:
        return _session()


# def init(engine, session):

# global _engine, _session
# _engine = engine
# _session = session

# import scimodom.database.models
# Base.metadata.create_all(engine)


# _engine = None
# _session = None


# class Base(DeclarativeBase):
# pass


def get_engine():
    if _engine is None:
        raise Exception("DB engine not created!")
    else:
        return _engine


# def get_session():
# if _session is None:
# raise Exception("Session not initialized!")
# else:
# return _session()


def init(engine, session):
    global _engine, _session
    _engine = engine
    _session = session

    import scimodom.database.models

    Base.metadata.create_all(engine)
