import fcntl
import logging
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar

from sqlalchemy import select, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from scimodom.config import Config
from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    Data,
    DataAnnotation,
    GenomicAnnotation,
    Taxa,
    Selection,
)
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.external import ExternalService
from scimodom.services.web import WebService

logger = logging.getLogger(__name__)


class AnnotationNotFoundError(Exception):
    """Exception handling for a non-existing Annotation
    or Annotation that is not the latest version."""

    pass


class GenericAnnotationService(ABC):
    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    ANNOTATION_PATH: ClassVar[str] = "annotation"
    CACHE_PATH: ClassVar[Path] = Path("cache", "gene", "selection")

    def __init__(
        self,
        session: Session,
        assembly_service: AssemblyService,
        data_service: DataService,
        bedtools_service: BedToolsService,
        external_service: ExternalService,
        web_service: WebService,
    ) -> None:
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
        :param web_service: Web Service instance
        :type web_service: WebService
        """

        self._session = session
        self._assembly_service = assembly_service
        self._data_service = data_service
        self._bedtools_service = bedtools_service
        self._external_service = external_service
        self._web_service = web_service

        self._version = self._session.execute(
            select(AnnotationVersion.version_num)
        ).scalar_one()

    def __new__(cls, session: Session, **kwargs):
        if cls.DATA_PATH is None:
            raise ValueError("Missing environment variable: DATA_PATH.")
        elif not Path(cls.DATA_PATH, cls.ANNOTATION_PATH).is_dir():
            raise FileNotFoundError(
                f"No such directory '{Path(cls.DATA_PATH, cls.ANNOTATION_PATH)}'."
            )
        if not Path(cls.DATA_PATH, cls.CACHE_PATH).is_dir():
            logger.warning(
                f"DATA PATH {Path(cls.DATA_PATH, cls.CACHE_PATH)} not found! Creating!"
            )
            Path(cls.DATA_PATH, cls.CACHE_PATH).mkdir(parents=True, mode=0o755)
        return super().__new__(cls)

    @staticmethod
    def get_annotation_path() -> Path:
        """Construct parent path to annotation files.

        :returns: Path to annotation
        :rtype: Path
        """
        return Path(
            GenericAnnotationService.DATA_PATH, GenericAnnotationService.ANNOTATION_PATH
        )

    @staticmethod
    def get_cache_path() -> Path:
        """Construct path to gene cache (selection).

        :returns: Path to gene cache
        :rtype: Path
        """
        return Path(
            GenericAnnotationService.DATA_PATH, GenericAnnotationService.CACHE_PATH
        )

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

    def update_gene_cache(self, eufid: str, selections: dict[int, int]) -> None:
        """Update gene cache.

        :param eufid: EUFID (dataset ID)
        :type eufid: str
        :param selections: Dict of selection ID(s): modification ID(s)
        :type selections: dict of {int: int}
        """
        cache_path = self.get_cache_path()
        for selection_id, modification_id in selections.items():
            query = select(Data.id).filter_by(
                dataset_id=eufid, modification_id=modification_id
            )
            data_ids = self._session.execute(query).scalars().all()
            query = (
                select(GenomicAnnotation.name)
                .join_from(
                    GenomicAnnotation, DataAnnotation, GenomicAnnotation.annotations
                )
                .where(DataAnnotation.data_id.in_(data_ids))
            ).distinct()
            genes = list(
                filter(
                    lambda g: g is not None,
                    set(self._session.execute(query).scalars().all()),
                )
            )

            with open(Path(cache_path, str(selection_id)), "w") as fc:
                fcntl.flock(fc.fileno(), fcntl.LOCK_EX)
                fc.write("\n".join(genes))
                fcntl.flock(fc.fileno(), fcntl.LOCK_UN)

    def get_release_path(self, annotation: Annotation) -> Path:
        """Construct annotation release path.

        :param annotation: Annotation instance
        :type annotation: Annotation
        :returns: Annotation release path
        :rtype: Path
        """
        organism_name = self._session.execute(
            select(Taxa.name).filter_by(id=annotation.taxa_id)
        ).scalar_one()
        organism_name = "_".join(organism_name.lower().split()).capitalize()
        assembly_name = self._assembly_service.get_name_for_version(annotation.taxa_id)
        path = self.get_annotation_path()
        return Path(path, organism_name, assembly_name, str(annotation.release))

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

    def _get_modification_from_selection(self, idx: int) -> int:
        return self._session.execute(
            select(Selection.modification_id).where(Selection.id == idx)
        ).scalar_one()

    def annotate_data(self, taxa_id: int, eufid: str, selection_ids: list[int]):
        self._annotate_data_in_database(taxa_id, eufid)
        selections = {
            idx: self._get_modification_from_selection(idx) for idx in selection_ids
        }
        self.update_gene_cache(eufid, selections)

    @abstractmethod
    def _annotate_data_in_database(self, taxa_id: int, eufid: str):
        pass
