"""Provide a generic class for the annotation service."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar

from sqlalchemy import func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from scimodom.database.models import (
    Annotation,
    AnnotationRelease,
    AnnotationVersion,
    Assembly,
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
    """Exception handling for a non-existing Annotation."""


class GenericAnnotationService(ABC):
    """General utility class to handle annotations.

    :param session: SQLAlchemy ORM session
    :param data_service: Data service instance
    :param bedtools_service: Bedtools service instance
    :param external_service: External service instance
    :param web_service: Web Service instance
    :param file_service: FileService
    """

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
        self._session = session
        self._data_service = data_service
        self._bedtools_service = bedtools_service
        self._external_service = external_service
        self._web_service = web_service
        self._gene_service = gene_service
        self._file_service = file_service

    @property
    def _version(self) -> str:
        """Current annotation version.

        This is read from the database on each access (not cached).
        """
        return self._session.execute(
            select(AnnotationVersion.version_num),
        ).scalar_one()

    @property
    def _is_current(self) -> ColumnElement[bool]:
        """Filter query for the current version.

        :return: column-oriented SQL expression, True if
        the annotation version is the current, False otherwise
        """
        return Annotation.version == self._version

    @abstractmethod
    def _annotate_data_in_database(self, taxa_id: int, dataset_id: str):
        pass

    def get_current_by_taxa_and_source(
        self,
        taxa_id: int,
        source: str,
    ) -> Annotation:
        """Retrieve the current annotation of a taxon by source.

        :param taxa_id: NCBI taxon
        :param source: Annotation source
        :raise: AnnotationNotFoundError
        :return: Annotation instance
        """
        try:
            return self._session.execute(
                select(Annotation)
                .join(Assembly, Annotation.inst_assembly)
                .where(
                    self._is_current,
                    Assembly.taxa_id == taxa_id,
                    Annotation.source == source,
                )
            ).scalar_one()
        except NoResultFound:
            raise AnnotationNotFoundError(
                f"No such {source} annotation for taxonomy ID: {taxa_id}."
            )

    def get_annotations(
        self,
        taxa_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get all current annotations of this source.

        A source that serves no browsable page for a release leaves
        `browse_url` null, e.g. EnsemblAnnotationService which
        overrides this.

        :param taxa_id: NCBI taxon or None
        :return: JSON array with extended annotations
        """
        query = (
            select(Annotation, AnnotationRelease, Assembly, Taxa)
            .join(Assembly, Annotation.inst_assembly)
            .join(Taxa, Assembly.inst_taxa)
            .join(AnnotationRelease, Annotation.inst_release)
            .where(
                self._is_current,
                Annotation.source == self.ANNOTATION_SOURCE,
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

        :param annotation: Annotation instance
        :return: Annotation release path
        """
        assembly = annotation.inst_assembly
        return self._file_service.get_annotation_release_dir(
            assembly.taxa_id,
            annotation.source,
            annotation.release,
            assembly_name=assembly.name,
        )

    def annotate_data(
        self,
        taxa_id: int,
        dataset_id: str,
        selection_ids: list[int],
    ) -> None:
        """Wrap data annotation.

        :param taxa_id: NCBI taxon
        :dataset_id: Dataset identifier
        :selection_ids: A list of associated selection identifiers
        """
        self._annotate_data_in_database(taxa_id, dataset_id)
        for selection_id in selection_ids:
            self._gene_service.update_gene_cache(selection_id)

    def _has_records(self, annotation: Annotation) -> bool:
        """Check if records exist for this annotation.

        The annotation table does not record the state of an annotation.
        This function asserts if the annotation has been set up
        by checking if the database contains GenomicAnnotation
        records for it, which are created by `create_current`.
        It is what makes the latter idempotent, so that re-running
        it does not duplicate records.

        :param annotation: Annotation instance
        :return: True if this annotation has genes in the database
        """
        length = self._session.scalar(
            select(func.count())
            .select_from(GenomicAnnotation)
            .filter_by(annotation_id=annotation.id)
        )
        logger.debug(f"Found {length} rows for annotation '{annotation.id}'")
        return length > 0
