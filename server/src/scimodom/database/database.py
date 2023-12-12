import os
from typing import Callable, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.engine import Engine

_engine = None
_session: Optional[Callable[[], Session]] = None


class Base(DeclarativeBase):
    pass


def make_session(database_uri: str) -> tuple[Engine, sessionmaker[Session]]:
    """Wrapper for engine creation and configurable Session factory.

    :param database_uri: Database URI
    :type database_uri: str
    :returns: engine and session
    :rtype: tuple(Engine, Session)
    """
    # options -> pool_recycle, isolation_level
    # connect_args={"check_same_thread": False}
    engine = create_engine(database_uri)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, session


def get_session():
    """Get current session."""
    if _session is None:
        raise Exception("Session not initialized!")
    else:
        return _session()


def get_engine():
    """Get engine."""
    if _engine is None:
        raise Exception("DB engine not created!")
    else:
        return _engine


def init(engine: Engine, session: Callable[[], Session]) -> None:
    """Set engine and session

    :param engine: Engine
    :type engine: Engine
    :param session: Session
    :type session: Callable[[], Session]
    """
    global _engine, _session
    _engine = engine
    _session = session
