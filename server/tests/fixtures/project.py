from datetime import datetime

import pytest

from scimodom.database.models import (
    ProjectContact,
    Project,
)


@pytest.fixture
def project(Session, setup):  # noqa
    session = Session()
    contact = ProjectContact(
        contact_name="Contact Name",
        contact_institution="Contact Institution",
        contact_email="Contact Email",
    )
    session.add(contact)
    session.flush()
    project = Project(
        id="12345678",
        title="Project Title",
        summary="Project summary",
        contact_id=contact.id,
        date_published=datetime.fromisoformat("2024-01-01"),
        date_added=datetime(2024, 6, 17, 12, 0, 0),
    )
    session.add(project)
    session.commit()
    yield project.id
