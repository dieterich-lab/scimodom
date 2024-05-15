from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from scimodom.services.permission import PermissionService
from scimodom.database.models import (
    User,
    UserState,
    Project,
    ProjectContact,
    UserProjectAssociation,
)


def test_insert_user_project_association(Session):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        user = User(email="contact@email", state=UserState.active, password_hash="xxx")
        session.add_all([contact, user])
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id

        service = PermissionService(Session())
        service.insert_into_user_project_association(user, smid)

        records = session.execute(select(UserProjectAssociation)).scalar()
        assert records.user_id == user.id
        assert records.project_id == smid
