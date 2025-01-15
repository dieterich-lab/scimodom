from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    GenomicAnnotation,
    DataAnnotation,
    Dataset,
    Data,
    Selection,
    DatasetModificationAssociation,
)
from scimodom.services.file import FileService, get_file_service


class GeneService:
    """Provide a service to facilitate handling of the gene cache.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param file_service: File service instance.
    :type file_service: FileService
    """

    def __init__(self, session: Session, file_service: FileService):
        self._session = session
        self._file_service = file_service

    def update_gene_cache(self, selection_id: int) -> None:
        """Update gene cache for one selection ID.

        :param selection_id: Selection ID
        :type selection_id: int
        """
        query = (
            select(GenomicAnnotation.name)
            .filter(Selection.id == selection_id)
            .filter(
                DatasetModificationAssociation.modification_id
                == Selection.modification_id
            )
            .filter(
                Dataset.id == DatasetModificationAssociation.dataset_id,
                Dataset.organism_id == Selection.organism_id,
                Dataset.technology_id == Selection.technology_id,
            )
            .filter(Data.dataset_id == Dataset.id)
            .filter(DataAnnotation.data_id == Data.id)
            .filter(GenomicAnnotation.id == DataAnnotation.gene_id)
        ).distinct()
        genes = list(
            filter(
                lambda g: g is not None,
                set(self._session.execute(query).scalars().all()),
            )
        )
        self._file_service.update_gene_cache(selection_id, genes)

    def get_genes(self, selection_ids: Iterable[int]) -> Iterable[str]:
        """Retrieve genes for multiple selection ID(s).

        :param selection_ids: List of selection ID(s)
        :type selection_id: Iterable[int]
        :returns: List of genes
        :rtype: Iterable[str]
        """
        result: set[str] = set()
        for selection_id in selection_ids:
            try:
                genes = self._file_service.get_gene_cache(selection_id)
            except FileNotFoundError:
                self.update_gene_cache(selection_id)
                genes = self._file_service.get_gene_cache(selection_id)
            result = result | set(genes)
        return sorted(list(result))

    def delete_gene_cache(self, selection_id: int) -> None:
        """Remove a gene cache file for a given selection.

        :param selection_id: Selection ID
        :type selection_id: int
        """
        self._file_service.delete_gene_cache(selection_id)


def get_gene_service() -> GeneService:
    """
    Create a GeneService by injecting dependencies.

    :returns: Gene service instance
    :rtype: GeneService
    """
    return GeneService(session=get_session(), file_service=get_file_service())
