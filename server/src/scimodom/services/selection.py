from functools import cache
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    DetectionMethod,
    DetectionTechnology,
    Modification,
    Modomics,
    Organism,
    ProjectSelection,
    RNAType,
    Selection,
    Taxa,
    Taxonomy,
)
from scimodom.services.gene import GeneService, get_gene_service
from scimodom.utils.dtos.project import ProjectMetaDataDto

logger = logging.getLogger(__name__)


class SelectionService:
    """Provide a service to handle selections.

    :param session: SQLAlchemy ORM session
    """

    def __init__(self, session: Session, gene_service: GeneService) -> None:
        self._session = session
        self._gene_service = gene_service

    def get_selections(self) -> list[dict[str, Any]]:
        """Get all selections.

        Selections are defined by an association:
        Modification, Organism, DetectionTechnology.

        :return: Selected columns from various ORM models
        describing each selection in detail.
        """
        query = self._get_selection_query(Selection).add_columns(
            Selection.id.label("selection_id")
        )
        return [row._asdict() for row in self._session.execute(query)]

    def get_project_selections(self, project_id: str) -> list[dict[str, Any]]:
        """Get the selections of a project.

        These are the combinations of modification, organism, and
        technology for which datasets can be added to the project.
        The result is the same as for get_selections, except that
        the selection ID is None if the selection does not exist
        (yet), i.e. if there is no dataset with this combination.

        NOTE: Return an empty list if the project_id does not exists
        or if no selections exist for this project.

        :param project_id: Project identifier (SMID).
        :return: Selected columns from various ORM models
        describing each selection in detail.
        """
        query = (
            self._get_selection_query(ProjectSelection)
            .add_columns(Selection.id.label("selection_id"))
            .join(
                Selection,
                and_(
                    Selection.modification_id == ProjectSelection.modification_id,
                    Selection.organism_id == ProjectSelection.organism_id,
                    Selection.technology_id == ProjectSelection.technology_id,
                ),
                isouter=True,
            )
            .where(ProjectSelection.project_id == project_id)
        )
        return [row._asdict() for row in self._session.execute(query)]

    def add_project_selections(
        self,
        project_id: str,
        metadata: list[ProjectMetaDataDto],
        is_flush_only: bool = False,
    ) -> None:
        """Declare the selections of a project.

        A project selection is a combination of modification, organism,
        and technology for which datasets may be added to the project.
        If it already exists, nothing is done. This does not create
        a selection (cf. get_or_create_selection), which only exists
        once there is data. Modifications, organisms, and technologies
        are created if they do not exist. The project metadata must be valid.

        :param project_id: Project identifier (SMID), the caller is
        responsible to reference a valid project identifier
        :param metadata: Validated project metadata
        :param is_flush_only: If True, flush w/o commit. Default is False.
        This can be useful if adding selections as part of a project,
        before a final commit is called.
        """
        try:
            for dto in metadata:
                modification_id = self._add_modification_if_none(dto)
                organism_id = self._add_organism_if_none(dto)
                technology_id = self._add_technology_if_none(dto)
                self._add_project_selection_if_none(
                    project_id, modification_id, organism_id, technology_id
                )
            if not is_flush_only:
                self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def get_or_create_selection(
        self, modification_id: int, organism_id: int, technology_id: int
    ) -> int:
        """Get a selection ID, create the selection if it does not exist.

        Flush w/o commit: the caller is responsible for the transaction.

        :param modification_id: Modification ID
        :param organism_id: Organism ID
        :param technology_id: Technology ID
        :return: Selection ID
        """
        selection = self._session.execute(
            select(Selection).filter_by(
                modification_id=modification_id,
                organism_id=organism_id,
                technology_id=technology_id,
            )
        ).scalar_one_or_none()
        if selection is None:
            selection = Selection(
                modification_id=modification_id,
                organism_id=organism_id,
                technology_id=technology_id,
            )
            self._session.add(selection)
            self._session.flush()
            logger.info(
                f"Flushed selection '{selection.id}' (m={modification_id}, "
                f"o={organism_id}, t={technology_id})."
            )
        return selection.id

    def delete_selections_by_dataset(self, dataset: Dataset) -> None:
        """Delete selection(s) associated with a Dataset and clear gene cache.

        This method is generally safe, i.e. if a selection is
        associated with at least one other dataset, only the gene
        cache is cleared. The gene cache is automatically
        regenerated on demand using the database.

        :param dataset: Dataset
        """
        modification_ids = [
            association.modification_id for association in dataset.associations
        ]
        selections = (
            self._session.execute(
                select(Selection).where(
                    Selection.modification_id.in_(modification_ids),
                    Selection.organism_id == dataset.organism_id,
                    Selection.technology_id == dataset.technology_id,
                )
            )
            .scalars()
            .all()
        )
        for selection in selections:
            cache_only = (
                self._session.execute(
                    select(Dataset.id)
                    .filter(Dataset.id != dataset.id)
                    .filter(Selection.id == selection.id)
                    .filter(
                        DatasetModificationAssociation.modification_id
                        == Selection.modification_id
                    )
                    .filter(
                        Dataset.id == DatasetModificationAssociation.dataset_id,
                        Dataset.organism_id == Selection.organism_id,
                        Dataset.technology_id == Selection.technology_id,
                    )
                ).first()
                is not None
            )
            self._delete_selection(selection, cache_only)

    @staticmethod
    def _get_selection_query(root: type[Selection] | type[ProjectSelection]):
        # root: any table with modification_id, organism_id, technology_id
        return (
            select(
                Modification.id.label("modification_id"),
                Modification.rna.label("rna_type"),
                RNAType.name.label("rna_type_name"),
                Modomics.short_name.label("modomics_short_name"),
                DetectionTechnology.id.label("technology_id"),
                DetectionMethod.cls,
                DetectionMethod.meth,
                DetectionTechnology.tech,
                Organism.id.label("organism_id"),
                Taxonomy.domain,
                Taxonomy.kingdom,
                Taxa.id.label("taxa_id"),
                Taxa.name.label("taxa_name"),
                Taxa.short_name.label("taxa_short_name"),
                Organism.cto,
            )
            .select_from(root)
            .join(Modification, Modification.id == root.modification_id)
            .join(DetectionTechnology, DetectionTechnology.id == root.technology_id)
            .join(Organism, Organism.id == root.organism_id)
            .join(Modomics, Modomics.id == Modification.modomics_id)
            .join(RNAType, RNAType.id == Modification.rna)
            .join(DetectionMethod, DetectionMethod.id == DetectionTechnology.method_id)
            .join(Taxa, Taxa.id == Organism.taxa_id)
            .join(Taxonomy, Taxonomy.id == Taxa.taxonomy_id)
        )

    def _add_project_selection_if_none(
        self,
        project_id: str,
        modification_id: int,
        organism_id: int,
        technology_id: int,
    ) -> None:
        exists = self._session.execute(
            select(ProjectSelection.id).filter_by(
                project_id=project_id,
                modification_id=modification_id,
                organism_id=organism_id,
                technology_id=technology_id,
            )
        ).scalar_one_or_none()
        if exists is None:
            self._session.add(
                ProjectSelection(
                    project_id=project_id,
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
            )
            self._session.flush()
            logger.info(
                f"Flushed selection for project '{project_id}' (m={modification_id}, "
                f"o={organism_id}, t={technology_id})."
            )

    def _add_modification_if_none(self, metadata: ProjectMetaDataDto) -> int:
        modification_id = self._session.execute(
            select(Modification.id).filter_by(
                rna=metadata.rna, modomics_id=metadata.modomics_id
            )
        ).scalar_one_or_none()
        if not modification_id:
            modification = Modification(
                rna=metadata.rna, modomics_id=metadata.modomics_id
            )
            self._session.add(modification)
            self._session.flush()
            modification_id = modification.id
        return modification_id

    def _add_organism_if_none(self, metadata: ProjectMetaDataDto) -> int:
        organism_id = self._session.execute(
            select(Organism.id).filter_by(
                cto=metadata.organism.cto, taxa_id=metadata.organism.taxa_id
            )
        ).scalar_one_or_none()
        if not organism_id:
            organism = Organism(
                cto=metadata.organism.cto, taxa_id=metadata.organism.taxa_id
            )
            self._session.add(organism)
            self._session.flush()
            organism_id = organism.id
        return organism_id

    def _add_technology_if_none(self, metadata: ProjectMetaDataDto) -> int:
        technology_id = self._session.execute(
            select(DetectionTechnology.id).filter_by(
                tech=metadata.tech, method_id=metadata.method_id
            )
        ).scalar_one_or_none()
        if not technology_id:
            technology = DetectionTechnology(
                tech=metadata.tech, method_id=metadata.method_id
            )
            self._session.add(technology)
            self._session.flush()
            technology_id = technology.id
        return technology_id

    def _delete_selection(self, selection: Selection, is_cache_only: bool) -> None:
        msg = (
            f"Removing selection '{selection.id}' (m={selection.modification_id}, "
            f"o={selection.organism_id}, t={selection.technology_id})..."
        )

        try:
            try:
                self._gene_service.delete_gene_cache(selection.id)
                msg = f"{msg}\n Deleted gene cache."
            except FileNotFoundError:
                msg = f"{msg}\n Gene cache not found."

            if not is_cache_only:
                self._session.delete(selection)
                self._session.commit()

                msg = f"{msg}\n Deleted selection from the database."

            logger.info(msg)

        except Exception:
            self._session.rollback()
            raise


@cache
def get_selection_service():
    """Instantiate a SelectionService object by injecting its dependencies.

    :returns: Selection service instance
    :rtype: SelectionService
    """
    return SelectionService(session=get_session(), gene_service=get_gene_service())
