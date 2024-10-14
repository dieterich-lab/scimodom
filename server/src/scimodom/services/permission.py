from functools import cache

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

import logging

from scimodom.database.database import get_session
from scimodom.database.models import User, Dataset, UserProjectAssociation

logger = logging.getLogger(__name__)


class PermissionService:
    def __init__(self, session: Session):
        self._session = session

    def may_change_dataset(self, user: User, dataset: Dataset) -> bool:
        """Check if user has permission to manage dataset.

        :param User: User
        :type User: User
        :param dataset: Dataset
        :type dataset: Dataset
        :returns: True if User has permission, else False
        :rtype: bool
        """
        query = select(UserProjectAssociation).where(
            and_(
                UserProjectAssociation.user_id == user.id,
                UserProjectAssociation.project_id == dataset.project_id,
            )
        )
        results = self._session.execute(query).fetchall()
        return len(results) > 0

    def insert_into_user_project_association(self, user: User, project_id: str) -> None:
        """Insert values into table.

        :param user: User
        :type user: User
        :param project_id: SMID. There is no type or value check,
        this must be done before calling this function.
        :type project_id: str
        """
        permission = UserProjectAssociation(user_id=user.id, project_id=project_id)

        logger.info(f"Adding user {user.email} to {project_id}")

        self._session.add(permission)
        self._session.commit()


@cache
def get_permission_service() -> PermissionService:
    return PermissionService(get_session())
