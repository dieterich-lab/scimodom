import os
from typing import Callable, Optional

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.engine import Engine

_engine = None
_session: Optional[Callable[[], Session]] = None


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


def make_session(database_uri: str) -> tuple[Engine, sessionmaker[Session]]:
    """Wrapper for engine creation and configurable Session factory.

    :param database_uri: Database URI
    :type database_uri: str
    :returns: engine and session
    :rtype: tuple(Engine, Session)
    """
    # https://docs.sqlalchemy.org/en/20/core/pooling.html#pool-disconnects
    # connect_args={"check_same_thread": False}
    engine = create_engine(database_uri, pool_pre_ping=True, pool_recycle=3600)
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
