from functools import cache

from sqlalchemy import select, exists, and_
from sqlalchemy.orm import Session

import logging

from scimodom.database.database import get_session
from scimodom.database.models import User, Dataset, UserProjectAssociation

logger = logging.getLogger(__name__)


class PermissionService:
    def __init__(self, session: Session):
        self._session = session

    def may_change_project(self, user: User, project_id: str) -> bool:
        """Check if user has permission to manage a project.

        :param user: User
        :param project_id: Project identifier (SMID)
        :return: True if User has permission, else False
        """
        query = select(UserProjectAssociation).where(
            and_(
                UserProjectAssociation.user_id == user.id,
                UserProjectAssociation.project_id == project_id,
            )
        )
        results = self._session.execute(query).fetchall()
        return len(results) > 0

    def may_change_dataset(self, user: User, dataset: Dataset) -> bool:
        """Check if user has permission to manage an existing dataset.

        :param User: User
        :param dataset: Dataset
        :return: True if User has permission, else False
        """
        return self.may_change_project(user, dataset.project_id)

    def insert_into_user_project_association(self, user: User, project_id: str) -> None:
        """Insert values into table.

        :param user: User
        :param project_id: A validated Project identifier (SMID).
        Validation must be performed by the caller.
        """
        is_found = self._session.query(
            exists().where(
                UserProjectAssociation.user_id == user.id,
                UserProjectAssociation.project_id == project_id,
            )
        ).scalar()
        if is_found:
            logger.info(f"User {user.email} already associated with {project_id}")
            return

        permission = UserProjectAssociation(user_id=user.id, project_id=project_id)

        logger.info(f"Adding user {user.email} to {project_id}")

        self._session.add(permission)
        self._session.commit()


@cache
def get_permission_service() -> PermissionService:
    return PermissionService(get_session())
