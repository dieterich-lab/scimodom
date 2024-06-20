import logging
from enum import Enum
from functools import cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from scimodom.database.database import get_session
from scimodom.database.models import (
    Annotation,
    RNAType,
    Modification,
)
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.annotation.generic import (
    GenericAnnotationService,
    AnnotationNotFoundError,
)
from scimodom.services.annotation.gtrnadb import GtRNAdbAnnotationService
from scimodom.services.assembly import get_assembly_service, AssemblyService
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.data import get_data_service, DataService
from scimodom.services.external import get_external_service, ExternalService
from scimodom.services.web import get_web_service

logger = logging.getLogger(__name__)


class AnnotationSource(Enum):
    ENSEMBL = "ensembl"
    GTRNADB = "gtrnadb"


RNA_TYPE_TO_ANNOTATION_SOURCE_MAP = {
    "WTS": AnnotationSource.ENSEMBL,
    "tRNA": AnnotationSource.GTRNADB,
}


class AnnotationService:
    """Utility class to handle annotations.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param assembly_service: Assembly service instance
    :type assembly service: AssemblyService
    :param data_service: Data service instance
    :type data service: DataService
    :param bedtools_service: Bedtools service instance
    :type bedtools_service: BedToolsService
    :param external_service: External service instance
    :type external_service: ExternalService
    :param DATA_PATH: Path to data
    :type DATA_PATH: str | Path
    :param ANNOTATION_PATH: Subpath to annotation
    :type ANNOTATION_PATH: str
    :param CACHE_PATH: Path to gene cache
    :type CACHE_PATH: Path
    """

    def __init__(
        self,
        session: Session,
        services_by_annotation_source: dict[AnnotationSource, GenericAnnotationService],
    ) -> None:
        """Initializer method."""
        self._session = session
        self._services_by_annotation_source = services_by_annotation_source

    def check_annotation_source(
        self, annotation_source: AnnotationSource, modification_ids: list[int]
    ) -> bool:
        rna_types = (
            self._session.execute(
                select(RNAType.id)
                .distinct()
                .join(Modification, RNAType.modifications)
                .where(Modification.id.in_(modification_ids))
            )
            .scalars()
            .all()
        )
        if len(rna_types) > 1:
            return False
        if RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[rna_types[0]] != annotation_source:
            return False
        return True

    def get_features(
        self, annotation_source: AnnotationSource
    ) -> dict[str, dict[str, str]]:
        return self._services_by_annotation_source[annotation_source].FEATURES

    def get_annotation(
        self, annotation_source: AnnotationSource, taxa_id: int
    ) -> Annotation:
        return self._services_by_annotation_source[annotation_source].get_annotation(
            taxa_id
        )

    def create_annotation(
        self, annotation_source: AnnotationSource, taxa_id: int, **kwargs
    ) -> Annotation:
        return self._services_by_annotation_source[annotation_source].create_annotation(
            taxa_id, **kwargs
        )

    def annotate_data(
        self,
        taxa_id: int,
        annotation_source: AnnotationSource,
        eufid: str,
        selection_ids: list[int],
    ):
        self._services_by_annotation_source[annotation_source].annotate_data(
            taxa_id, eufid, selection_ids
        )


@cache
def get_annotation_service() -> AnnotationService:
    """Helper function to set up an AnnotationService object by injecting its dependencies."""
    session = get_session()
    assembly_service = get_assembly_service()
    data_service = get_data_service()
    bedtools_service = get_bedtools_service()
    external_service = get_external_service()
    web_service = get_web_service()
    return AnnotationService(
        session=session,
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=session,
                assembly_service=assembly_service,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
            ),
            AnnotationSource.GTRNADB: GtRNAdbAnnotationService(
                session=session,
                assembly_service=assembly_service,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
            ),
        },
    )
