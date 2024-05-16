from typing import List, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Association,
    Dataset,
    DetectionTechnology,
    Modomics,
    Modification,
    Organism,
    Project,
    Selection,
    Taxa,
    ProjectSource,
    User,
    UserProjectAssociation,
)


class DatasetService:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, eufid: str) -> Dataset:
        """Retrieve dataset by EUFID.

        :param eufid: EUFID
        :type eufid: str
        :returns: Query result
        :rtype: list of dict
        """
        return self._session.scalars(select(Dataset).where(Dataset.id == eufid)).one()

    def get_datasets(self, user: Optional[User] = None) -> List[Dict[str, str]]:
        """Retrieve all datasets. Add project-related information.

        :param user: Restricts results based on projects assotiated with user.
        :type user: User
        :returns: Query result
        :rtype: list of dict
        """

        query = (
            select(
                Dataset.project_id,
                Dataset.id.label("dataset_id"),
                Dataset.title.label("dataset_title"),
                Dataset.sequencing_platform,
                Dataset.basecalling,
                Dataset.bioinformatics_workflow,
                Dataset.experiment,
                Project.title.label("project_title"),
                Project.summary.label("project_summary"),
                func.group_concat(ProjectSource.doi.distinct()).label("doi"),
                func.group_concat(ProjectSource.pmid.distinct()).label("pmid"),
                Modification.rna,
                func.group_concat(Modomics.short_name.distinct()).label(
                    "modomics_sname"
                ),
                DetectionTechnology.tech,
                Taxa.short_name.label("taxa_sname"),
                Taxa.id.label("taxa_id"),
                Organism.cto,
            )
            .join_from(
                Dataset,
                Project,
                Dataset.project_id == Project.id,
            )
            .join_from(
                Project,
                ProjectSource,
                Project.id == ProjectSource.project_id,
                isouter=True,
            )
            .join_from(Dataset, Association, Dataset.id == Association.dataset_id)
            .join_from(Association, Selection, Association.selection_id == Selection.id)
            .join_from(
                Selection, Modification, Selection.modification_id == Modification.id
            )
            .join_from(
                Selection,
                DetectionTechnology,
                Selection.technology_id == DetectionTechnology.id,
            )
            .join_from(Selection, Organism, Selection.organism_id == Organism.id)
            .join_from(Modification, Modomics, Modification.modomics_id == Modomics.id)
            .join_from(Organism, Taxa, Organism.taxa_id == Taxa.id)
        )
        if user is not None:
            query = (
                query.join(
                    UserProjectAssociation,
                    UserProjectAssociation.project_id == Project.id,
                )
                .join(User, User.id == UserProjectAssociation.user_id)
                .where(User.id == user.id)
            )
        query = query.group_by(Dataset.project_id, Dataset.id)
        return [row._asdict() for row in self._session.execute(query)]


_cached_dataset_service: Optional[DatasetService] = None


def get_dataset_service():
    """Helper function to set up a DatasetService object by injecting its dependencies.

    :returns: Dataset service instance
    :rtype: DatasetService
    """
    global _cached_dataset_service
    if _cached_dataset_service is None:
        _cached_dataset_service = DatasetService(session=get_session())
    return _cached_dataset_service
