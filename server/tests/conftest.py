import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from scimodom.database.database import init, Base

pytest_plugins = [
    "tests.fixtures.setup",
    "tests.fixtures.selection",
    "tests.fixtures.project",
    "tests.fixtures.dataset",
    "tests.fixtures.bam_file",
]


@pytest.fixture()
def Session():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = scoped_session(session)
    init(engine, lambda: session)
    Base.metadata.create_all(engine)

    yield session

    session().rollback()
    session().close()
