from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import User, Dataset, UserProjectAssociation


class PermissionService:
    def __init__(self, session: Session):
        self._db_session = session

    def may_attach_to_dataset(self, user: User, dataset: Dataset) -> bool:
        query = select(UserProjectAssociation).where(
            and_(
                UserProjectAssociation.user_id == user.id,
                UserProjectAssociation.project_id == dataset.project_id,
            )
        )
        results = self._db_session.execute(query).fetchall()
        return len(results) > 0


_cached_permission_service: Optional[PermissionService] = None


def get_permission_service() -> PermissionService:
    global _cached_permission_service
    if _cached_permission_service is None:
        _cached_permission_service = PermissionService(get_session())
    return _cached_permission_service
