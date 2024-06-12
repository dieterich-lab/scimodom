from functools import cache
from typing import List, Dict, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    DetectionTechnology,
    Modomics,
    Modification,
    Organism,
    Project,
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

        :param user: Restricts results based on projects associated with user.
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
            .join_from(Dataset, Project, Dataset.inst_project)
            .join_from(
                Project,
                ProjectSource,
                Project.sources,
                isouter=True,
            )
            .join_from(Dataset, DatasetModificationAssociation, Dataset.associations)
            .join_from(
                DatasetModificationAssociation,
                Modification,
                DatasetModificationAssociation.inst_modification,
            )
            .join_from(Modification, Modomics, Modification.inst_modomics)
            .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
            .join_from(Dataset, Organism, Dataset.inst_organism)
            .join_from(Organism, Taxa, Organism.inst_taxa)
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


@cache
def get_dataset_service() -> DatasetService:
    """Helper function to set up a DatasetService object by injecting its dependencies.

    :returns: Dataset service instance
    :rtype: DatasetService
    """
    return DatasetService(session=get_session())
