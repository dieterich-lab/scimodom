import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.database.models import (
    Assembly,
    Annotation,
    AnnotationRelease,
    AnnotationVersion,
    GenomicAnnotation,
    Taxa,
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
    or Annotation that is not the current version."""

    pass


class GenericAnnotationService(ABC):
    # the AnnotationSource this service handles, cf.
    # scimodom.utils.specs.enums.AnnotationSource
    ANNOTATION_SOURCE: ClassVar[str]

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

    @property
    def _version(self) -> str:
        """Current annotation (database) version.

        This is read from the database on each access (not cached),
        as for the assembly version: an upgrade changes it, and a
        service built once at start-up would otherwise keep handing
        out the version it saw then.
        """
        return self._session.execute(select(AnnotationVersion.version_num)).scalar_one()

    def get_by_taxa_and_source(self, taxa_id: int, source: str) -> Annotation:
        """Retrieve the current annotation of an organism and source.

        NOTE: this returns one annotation, cf. get_annotations for
        the catalog of all of them.

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
                select(Annotation)
                .join(Assembly, Annotation.inst_assembly)
                .where(
                    Assembly.taxa_id == taxa_id,
                    Annotation.source == source,
                    Annotation.version == self._version,
                )
            ).scalar_one()
        except NoResultFound:
            raise AnnotationNotFoundError(
                f"No such {source} annotation for taxonomy ID: {taxa_id}."
            )

    def get_annotations(self, taxa_id: int | None = None) -> list[dict[str, Any]]:
        """Get the current annotations of this source.

        Only the annotations in use are listed: a retired annotation
        no longer has data in the database, cf. get_by_taxa_and_source.

        The release is that of the annotation, not of the assembly:
        an annotation-only upgrade moves one and not the other.

        A source that serves no browsable page for a release leaves
        `browse_url` null, cf. EnsemblAnnotationService which
        overrides this.

        :param taxa_id: Taxonomy ID, or None for every organism
        :return: Annotations
        """
        query = (
            select(Annotation, AnnotationRelease, Assembly, Taxa)
            .join(Assembly, Annotation.inst_assembly)
            .join(Taxa, Assembly.inst_taxa)
            .join(AnnotationRelease, Annotation.inst_release)
            .where(
                Annotation.source == self.ANNOTATION_SOURCE,
                Annotation.version == self._version,
            )
        )
        if taxa_id is not None:
            query = query.where(Assembly.taxa_id == taxa_id)
        return [
            {
                "id": row.Annotation.id,
                "source": row.Annotation.source,
                "release": row.Annotation.release,
                "archive": row.AnnotationRelease.archive,
                "browse_url": None,
                "assembly_id": row.Assembly.id,
                "assembly_name": row.Assembly.name,
                "taxa_id": row.Taxa.id,
                "taxa_name": row.Taxa.name,
            }
            for row in self._session.execute(query.order_by(Assembly.taxa_id))
        ]

    def get_release_path(self, annotation: Annotation) -> Path:
        """Construct annotation release path.

        The assembly comes from the annotation, so the path does not
        depend on which assembly is current.

        :param annotation: Annotation instance
        :type annotation: Annotation
        :returns: Annotation release path
        :rtype: Path
        """
        assembly = annotation.inst_assembly
        return self._file_service.get_annotation_release_dir(
            assembly.taxa_id,
            annotation.source,
            annotation.release,
            assembly_name=assembly.name,
        )

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

    def annotate_data(self, taxa_id: int, dataset_id: str, selection_ids: list[int]):
        self._annotate_data_in_database(taxa_id, dataset_id)
        for selection_id in selection_ids:
            self._gene_service.update_gene_cache(selection_id)

    @abstractmethod
    def _annotate_data_in_database(self, taxa_id: int, dataset_id: str):
        pass
