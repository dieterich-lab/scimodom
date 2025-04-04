import logging
from abc import ABC, abstractmethod
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
)
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.external import ExternalService
from scimodom.services.file import FileService
from scimodom.services.gene import GeneService
from scimodom.services.web import WebService

logger = logging.getLogger(__name__)


class AnnotationNotFoundError(Exception):
    """Exception handling for a non-existing Annotation
    or Annotation that is not the latest version."""

    pass


class GenericAnnotationService(ABC):
    def __init__(
        self,
        session: Session,
        data_service: DataService,
        bedtools_service: BedToolsService,
        external_service: ExternalService,
        web_service: WebService,
        gene_service: GeneService,
        file_service: FileService,
    ) -> None:
        """Utility class to handle annotations.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param data_service: Data service instance
        :type data service: DataService
        :param bedtools_service: Bedtools service instance
        :type bedtools_service: BedToolsService
        :param external_service: External service instance
        :type external_service: ExternalService
        :param web_service: Web Service instance
        :type web_service: WebService
        :param file_service: FileService
        :type file_service: FileService
        """

        self._session = session
        self._data_service = data_service
        self._bedtools_service = bedtools_service
        self._external_service = external_service
        self._web_service = web_service
        self._gene_service = gene_service
        self._file_service = file_service

        self._version = self._session.execute(
            select(AnnotationVersion.version_num)
        ).scalar_one()

    def get_annotation_from_taxid_and_source(
        self, taxa_id: int, source: str
    ) -> Annotation:
        """Retrieve annotation from taxonomy ID and source
        for the latest database version.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param source: Annotation source
        :type source: str
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        try:
            return self._session.execute(
                select(Annotation).filter_by(
                    taxa_id=taxa_id, source=source, version=self._version
                )
            ).scalar_one()
        except NoResultFound:
            raise AnnotationNotFoundError(
                f"No such {source} annotation for taxonomy ID: {taxa_id}."
            )

    def get_release_path(self, annotation: Annotation) -> Path:
        """Construct annotation release path.

        :param annotation: Annotation instance
        :type annotation: Annotation
        :returns: Annotation release path
        :rtype: Path
        """
        path = self._file_service.get_annotation_dir(annotation.taxa_id)
        return Path(path, str(annotation.release))

    def _release_exists(self, annotation_id) -> bool:
        """Check if release exists by checking if the database
        contains records for this release."""
        length = self._session.scalar(
            select(func.count())
            .select_from(GenomicAnnotation)
            .filter_by(annotation_id=annotation_id)
        )
        logger.debug(f"Found {length} rows for annotation {annotation_id}.")
        if length > 0:
            return True
        return False

    def annotate_data(self, taxa_id: int, eufid: str, selection_ids: list[int]):
        self._annotate_data_in_database(taxa_id, eufid)
        for selection_id in selection_ids:
            self._gene_service.update_gene_cache(selection_id)

    @abstractmethod
    def _annotate_data_in_database(self, taxa_id: int, eufid: str):
        pass
