import fcntl
import logging
from pathlib import Path
from posixpath import join as urljoin
import shutil
from typing import ClassVar, Callable

import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import select, exists

from scimodom.config import Config
import scimodom.database.queries as queries
from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import (
    Annotation,
    Assembly,
    Data,
    DataAnnotation,
    GenomicAnnotation,
    Taxa,
)
from scimodom.services.assembly import AssemblyService
from scimodom.services.importer.base import MissingDataError
from scimodom.services.bedtools import BedToolsService
import scimodom.utils.specifications as specs
from scimodom.services.modification import ModificationService

logger = logging.getLogger(__name__)


class InstantiationError(Exception):
    """Exception handling for AnnotationService instantiation."""

    pass


class AnnotationVersionError(Exception):
    """Exception handling for Annotation version mismatch."""

    pass


class AnnotationFormatError(Exception):
    """Exception handling for Annotation format mismatch."""

    pass


class AnnotationService:
    """Utility class to handle annotations.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param annotation_id: Annotation ID
    :type annotation_id: str
    :param taxid: Taxa ID
    :type taxid: int
    :param DATA_PATH: Path to annotation
    :type DATA_PATH: str | Path | None
    :param DATA_SUB_PATH: Subpath to annotation file
    :type DATA_SUB_PATH: str
    :param FMT: Annotation file format
    :type FMT: str
    """

    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    DATA_SUB_PATH: ClassVar[str] = "annotation"
    DATA_GENE_CACHE_PATH: ClassVar[Path] = Path("cache", "gene", "selection")
    FMT: ClassVar[str] = "gtf"  # only handles GTF
    ANNOTATION_FILE: ClassVar[
        Callable
    ] = "{organism}.{assembly}.{release}.chr.{fmt}.gz".format
    FEATURES: ClassVar[dict[str, dict[str, str]]] = {
        "conventional": {
            "exon": "Exonic",
            "five_prime_utr": "5'UTR",
            "three_prime_utr": "3'UTR",
            "CDS": "CDS",
        },
        "extended": {"intron": "Intronic", "intergenic": "Intergenic"},
    }

    def __init__(
        self,
        session: Session,
        bedtools_service: BedToolsService,
        modification_service: ModificationService,
        **kwargs,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._bedtools_service = bedtools_service
        self._modification_service = modification_service

        self._annotation_id: int
        self._db_version: str
        self._taxid: int
        self._release: int
        self._annotation_file: Path
        self._chrom_file: Path

        # current DB annotation version
        query = queries.get_annotation_version()
        self._db_version = self._session.execute(query).scalar()

        annotation_id = kwargs.get("annotation_id", None)
        taxa_id = kwargs.get("taxa_id", None)
        if annotation_id is not None:
            is_found = self._session.query(
                exists().where(Annotation.id == annotation_id)
            ).scalar()
            if not is_found:
                msg = (
                    f"Annotation ID = {annotation_id} not found! Aborting transaction!"
                )
                raise InstantiationError(msg)
            self._annotation_id = annotation_id
            query = queries.query_column_where(
                Annotation,
                ["version", "release", "taxa_id"],
                filters={"id": self._annotation_id},
            )
            records = self._session.execute(query).one()
            version = records[0]
            # forbid instantiation for "other" annotation versions
            if not version == self._db_version:
                msg = (
                    f"Mismatch between current DB annotation version ({self._db_version}) and "
                    f"version ({version}) from annotation ID = {self._annotation_id}. Aborting transaction!"
                )
                raise AnnotationVersionError(msg)
            self._release = records[1]
            self._taxid = records[2]
        elif taxa_id is not None:
            is_found = self._session.query(exists().where(Taxa.id == taxa_id)).scalar()
            if not is_found:
                msg = f"Taxonomy ID = {taxa_id} not found! Aborting transaction!"
                raise InstantiationError(msg)
            self._taxid = taxa_id
            query = queries.query_column_where(
                Annotation,
                ["id", "release"],
                filters={"taxa_id": self._taxid, "version": self._db_version},
            )
            records = self._session.execute(query).one()
            self._annotation_id = records[0]
            self._release = records[1]

        self._get_files_path()

    def __new__(cls, session: Session, **kwargs):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        else:
            if not Path(cls.DATA_PATH, cls.DATA_GENE_CACHE_PATH).is_dir():
                msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_GENE_CACHE_PATH)} not found! Creating!"
                logger.warning(msg)
                Path(cls.DATA_PATH, cls.DATA_GENE_CACHE_PATH).mkdir(
                    parents=True, mode=0o755
                )
            return super(AnnotationService, cls).__new__(cls)

    @staticmethod
    def get_annotation_path() -> Path:
        """Construct parent path to annotation files.

        :returns: Path to annotation
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.DATA_SUB_PATH)

    @staticmethod
    def get_gene_cache_path() -> Path:
        """Construct path to gene cache (selection).

        :returns: Path to gene cache
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.DATA_GENE_CACHE_PATH)

    def create_annotation(self) -> None:
        """Create destination, download gene annotation,
        wrangle and write annotation to disk and to database.

        If destination exists, the first record for the current
        annotation is queried. If there are no records, raises
        a FileExistsError (annotation file exists, but the database
        does not appear to have been updated), else nothing
        is done (it is assumed that the database has been updated).
        If the destination does not exist, it is created.
        """
        parent = self._annotation_file.parent
        filen = self._annotation_file.name
        organism_name = filen.split(".")[0].lower()

        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            msg = f"Annotation directory {parent} already exists..."
            logger.info(msg)
            query = select(GenomicAnnotation).where(
                GenomicAnnotation.annotation_id == self._annotation_id
            )
            if self._session.execute(query).first() is None:
                msg = (
                    f"{msg} but there is no record in GenomicAnnotation matching "
                    f"the current annotation {self._annotation_id} ({self._taxid}, {self._release}). "
                    "Aborting transaction!"
                )
                raise Exception(msg) from exc
            return

        try:
            self._download_annotation()
            features = {k: list(v.keys()) for k, v in self.FEATURES.items()}
            self._bedtools_service.write_annotation_to_bed(
                self._annotation_file, self._chrom_file, features
            )
            self._create_annotation()
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(parent)
            raise

    def annotate_data(self, eufid: str) -> None:
        """Annotate Data: add entries to DataAnnotation
        for a given dataset.

        :param eufid: EUF ID
        :type eufid: str
        """
        logger.debug(f"Annotating records for EUFID {eufid}...")
        records = list(self._modification_service.get_modifications_by_dataset(eufid))
        if len(records) == 0:
            raise MissingDataError(f"[Annotation] No records found for {eufid}... ")

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = self._bedtools_service.annotate_data_to_records(
            self._annotation_file.parent, features, records
        )
        with InsertBuffer[DataAnnotation](self._session) as buffer:
            for record in annotated_records:
                buffer.queue(DataAnnotation(**record.model_dump()))
        self._session.flush()

    def update_gene_cache(self, eufid: str, selections: dict[int, int]) -> None:
        """Update gene cache.

        :param eufid: EUFID (dataset ID)
        :type eufid: str
        :param selections: Dict of selection ID(s): modification ID(s)
        :type selections: dict of {int: int}
        """
        cache_path = self.get_gene_cache_path()
        for selection_id, modification_id in selections.items():
            query = select(Data.id).where(
                Data.dataset_id == eufid, Data.modification_id == modification_id
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

    def _get_files_path(self) -> None:
        """Construct file path (annotation and chrom files) for
        the current annotation."""
        query = queries.query_column_where(Taxa, "name", filters={"id": self._taxid})
        organism_name = self._session.execute(query).scalar_one()
        organism_name = "_".join(organism_name.lower().split()).capitalize()
        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, "name", filters={"taxa_id": self._taxid, "version": version}
        )
        assembly_name = self._session.execute(query).scalar_one()
        path = self.get_annotation_path()
        parent = Path(path, organism_name, assembly_name, str(self._release))
        filen = self.ANNOTATION_FILE(
            organism=organism_name,
            assembly=assembly_name,
            release=self._release,
            fmt=self.FMT,
        )
        self._annotation_file = Path(parent, filen)
        parent, filen = AssemblyService.get_chrom_path(organism_name, assembly_name)
        self._chrom_file = Path(parent, filen)

    def _download_annotation(self) -> None:
        """Download gene annotation."""

        msg = "Downloading annotation info..."
        logger.info(msg)

        filen = self._annotation_file.name
        organism_name = filen.split(".")[0].lower()
        url = urljoin(
            specs.ENSEMBL_FTP,
            f"release-{self._release}",
            self.FMT,
            organism_name,
            filen,
        )
        with requests.get(url, stream=True) as request:
            if not request.ok:
                request.raise_for_status()
            with open(self._annotation_file, "wb") as fh:
                for chunk in request.iter_content(chunk_size=10 * 1024):
                    fh.write(chunk)

    def _create_annotation(self) -> None:
        """Reads annotation file to records and
        insert to GenomicAnnotation."""
        records = self._bedtools_service.get_annotation_records(
            self._annotation_file,
            self._annotation_id,
            self.FEATURES["extended"]["intergenic"],
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))
