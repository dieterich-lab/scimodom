from datetime import datetime

import pytest

from scimodom.database.models import (
    ProjectContact,
    ProjectSource,
    Project,
    User,
    UserProjectAssociation,
)
from scimodom.utils.specs.enums import UserState


@pytest.fixture
def project(Session):  # noqa
    session = Session()
    contact1 = ProjectContact(
        contact_name="Contact Name",
        contact_institution="Contact Institution",
        contact_email="contact@email",
    )
    contact2 = ProjectContact(
        contact_name="Contact Name 2",
        contact_institution="Contact Institution 2",
        contact_email="contact2@email",
    )
    session.add_all([contact1, contact2])
    session.flush()
    project1 = Project(
        id="12345678",
        title="Project Title",
        summary="Project summary",
        contact_id=contact1.id,
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
    project2 = Project(
        id="ABCDEFGH",
        title="Project Title 2",
        summary="Project summary 2",
        contact_id=contact2.id,
        date_added=datetime(2024, 6, 17, 12, 0, 0),
    )
    # add user
    user = User(email=contact1.contact_email, state=UserState.wait_for_confirmation)
    session.add(user)
    session.flush()
    association = UserProjectAssociation(user_id=user.id, project_id=project1.id)
    session.add_all([project1, source1, source2, association, project2])
    session.commit()
    yield (project1, project2)
