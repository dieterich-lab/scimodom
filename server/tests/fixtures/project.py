from datetime import datetime

import pytest

from scimodom.database.models import (
    ProjectContact,
    ProjectSource,
    Project,
    User,
    UserProjectAssociation,
    UserState,
)


@pytest.fixture
def project(Session, setup):  # noqa
    session = Session()
    contact = ProjectContact(
        contact_name="Contact Name",
        contact_institution="Contact Institution",
        contact_email="contact@email",
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
    source1 = ProjectSource(
        project_id="12345678",
        doi="doi1",
        pmid=12345678,
    )
    source2 = ProjectSource(
        project_id="12345678",
        doi="doi2",
    )
    # add user
    user = User(email=contact.contact_email, state=UserState.wait_for_confirmation)
    session.add(user)
    session.flush()
    association = UserProjectAssociation(user_id=user.id, project_id=project.id)
    session.add_all([project, source1, source2, association])
    session.commit()
    yield project
