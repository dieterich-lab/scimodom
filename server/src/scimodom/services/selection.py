from functools import cache
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Dataset,
    DatasetModificationAssociation,
    Modification,
    DetectionTechnology,
    Organism,
    Selection,
)
from scimodom.services.gene import GeneService, get_gene_service
from scimodom.utils.dtos.project import ProjectMetaDataDto

logger = logging.getLogger(__name__)


class SelectionService:
    """Provide a service to handle selections.

    :param session: SQLAlchemy ORM session
    :type session: Session
    """

    def __init__(self, session: Session, gene_service: GeneService) -> None:
        self._session = session
        self._gene_service = gene_service

    def create_selection(
        self, metadata: list[ProjectMetaDataDto], is_flush_only: bool = False
    ) -> None:
        """Add a new selection to the database.

        If a selection already exists, nothing is done.
        The project metadata template must be a valid template
        with valid entries.

        :param metadata: Validated project metadata
        :type metadata: list of ProjectMetadataDto
        :param is_flush_only: If True, flush w/o commit. Default is False.
        This can be useful if adding a selection as part of a project,
        before a final commit is called.
        :type is_flush_only: bool
        :raises Exception: If fail to add selection.
        :return: Selection (newly create or existing)
        :rtype: Selection
        """
        try:
            self._flush_selections(metadata)
            if not is_flush_only:
                self._session.commit()
        except Exception:
            self._session.rollback()
            raise

    def delete_selections_by_dataset(self, dataset: Dataset) -> None:
        """Delete selection(s) associated with a Dataset and clear gene cache.

        This method is generally safe, i.e. if a selection is
        associated with at least one other dataset, only the gene
        cache is cleared. The gene cache is automatically
        regenerated on demand using the database.

        :param dataset: Dataset
        :type dataset: Dataset
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

    def _flush_selections(self, metadata: list[ProjectMetaDataDto]) -> None:
        for dto in metadata:
            modification_id = self._add_modification_if_none(dto)
            organism_id = self._add_organism_if_none(dto)
            technology_id = self._add_technology_if_none(dto)
            selection = self._session.execute(
                select(Selection).filter_by(
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
            ).scalar_one_or_none()
            if not selection:
                selection = Selection(
                    modification_id=modification_id,
                    organism_id=organism_id,
                    technology_id=technology_id,
                )
                self._session.add(selection)
                self._session.flush()

                logger.info(
                    f"Flushed selection '{selection.id}' "
                    f"(m={modification_id}, o={organism_id}, t={technology_id})."
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
            self._gene_service.delete_gene_cache(selection.id)

            msg = f"{msg}\n Deleted gene cache."

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
