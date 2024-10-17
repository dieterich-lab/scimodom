import pytest
from sqlalchemy import select, func

from scimodom.services.permission import PermissionService
from scimodom.database.models import (
    User,
    UserProjectAssociation,
)
from scimodom.utils.specs.enums import UserState


def test_insert_user_project_association(Session, project):
    with Session() as session, session.begin():
        project_id = project[1].id
        user = User(email="contact2@email", state=UserState.active, password_hash="xxx")
        session.add(user)
        session.flush()
        user_id = user.id

        service = PermissionService(session)
        service.insert_into_user_project_association(user, project_id)

    with Session() as session, session.begin():
        assert (
            session.scalar(select(func.count()).select_from(UserProjectAssociation))
            == 2
        )
        records = session.execute(
            select(UserProjectAssociation).filter_by(project_id=project_id)
        ).scalar()
        assert records.user_id == user_id


def test_may_change_dataset(Session, dataset, project):  # noqa
    service = PermissionService(Session())
    with Session() as session, session.begin():
        user = session.get_one(User, 1)
        assert service.may_change_dataset(user, dataset[0]) is True
        assert service.may_change_dataset(user, dataset[3]) is False
