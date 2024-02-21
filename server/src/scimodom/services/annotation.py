# import gzip
import logging

# import os
from pathlib import Path
from posixpath import join as urljoin
from typing import ClassVar, Callable

# import zlib
import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy import select, insert

from scimodom.config import Config
import scimodom.database.queries as queries
from scimodom.database.models import (
    Annotation,
    Assembly,
    Association,
    Data,
    DataAnnotation,
    GenomicAnnotation,
    Taxa,
)
from scimodom.services.assembly import AssemblyService
from scimodom.services.importer import get_buffer
from scimodom.utils.operations import (
    write_annotation_to_bed,
    get_annotation_records,
    annotate_data_to_records,
)
from scimodom.utils.models import records_factory
import scimodom.utils.specifications as specs

logger = logging.getLogger(__name__)


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

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        self._session = session

        self._annotation_id: int
        self._db_versiob: str
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
            query = select(Annotation.id)
            if annotation_id not in self._session.execute(query).scalars().all():
                msg = (
                    f"Annotation ID = {annotation_id} not found! Aborting transaction!"
                )
                raise ValueError(msg)
            self._annotation_id = annotation_id
            query = queries.query_column_where(
                Annotation,
                ["version", "release", "taxa_id"],
                filters={"id": self._annotation_id},
            )
            records = [r._asdict() for r in self._session.execute(query)][0]
            version = records["version"]
            # forbid instantiation for "other" annotation versions
            if not version == self._db_version:
                msg = (
                    f"Mismatch between current DB annotation version ({self._db_version}) and "
                    f"version ({version}) from annotation ID = {self._annotation_id}. Aborting transaction!"
                )
                raise AnnotationVersionError(msg)
            self._release = records["release"]
            self._taxid = records["taxa_id"]
        elif taxa_id is not None:
            query = select(Taxa.id)
            if taxa_id not in self._session.execute(query).scalars().all():
                msg = f"Taxonomy ID = {taxa_id} not found! Aborting transaction!"
                raise ValueError(msg)
            self._taxid = taxa_id
            query = queries.query_column_where(
                Annotation,
                ["id", "release"],
                filters={"taxa_id": self._taxid, "version": self._db_version},
            )
            records = [r._asdict() for r in self._session.execute(query)][0]
            self._annotation_id = records["id"]
            self._release = records["release"]

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
            return super(AnnotationService, cls).__new__(cls)

    @staticmethod
    def get_annotation_path() -> Path:
        """Construct parent path to annotation files.

        :returns: Path to annotation
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.DATA_SUB_PATH)

    def create_annotation(self) -> None:
        """Create destination, download gene annotation,
        wrangle and write annotation to disk and to database.
        """
        ret_code = self._download_annotation()
        if ret_code == 0:
            features = {k: list(v.keys()) for k, v in self.FEATURES.items()}
            write_annotation_to_bed(
                self._annotation_file, self._chrom_file, features, AnnotationFormatError
            )
            self._create_annotation()

    def annotate_data(self, eufid: str) -> None:
        """Annotate Data: add entries to DataAnnotation

        :param eufid: EUF ID
        :type eufid: str
        """
        query = (
            select(
                Data.chrom,
                Data.start,
                Data.end,
                Data.name,
                Data.score,
                Data.strand,
                Data.id,
            )
            .join_from(Data, Association, Data.inst_association)
            .where(Association.dataset_id == eufid)
        )
        records = self._session.execute(query).all()

        msg = f"Annotating records for EUFID {eufid}..."
        logger.debug(msg)

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = annotate_data_to_records(
            self._annotation_file.parent, features, records, AnnotationFormatError
        )
        typed_annotated_records = [
            records_factory("DataAnnotation", r)._asdict() for r in annotated_records
        ]
        buffer = get_buffer(DataAnnotation)
        for record in typed_annotated_records:
            buffer.buffer_data(record)
        buffer.flush()
        self._session.commit()

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
        """Download gene annotation. If the destination already
        exists, the first record for the current annotation
        is queried. If None, this raises a FileExistsError
        (annotation file exists, but the database does not
        appear to have been updated). If not None, nothing
        is done, there is no further check. If the destination
        does not exist, it is created.
        """
        parent = self._annotation_file.parent
        filen = self._annotation_file.name
        organism_name = filen.split(".")[0].lower()
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            msg = f"Annotation directory {parent} already exists..."
            logger.debug(msg)
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
            return 1

        msg = "Downloading annotation info..."
        logger.debug(msg)

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
        return 0

    def _create_annotation(self) -> None:
        """Reads annotation file to records and
        insert to GenomicAnnotation."""
        query = select(GenomicAnnotation).where(
            GenomicAnnotation.annotation_id == self._annotation_id
        )
        records = get_annotation_records(
            self._annotation_file,
            self._annotation_id,
            self.FEATURES["extended"]["intergenic"],
        )
        typed_records = [
            records_factory("GenomicAnnotation", r)._asdict() for r in records
        ]
        buffer = get_buffer(GenomicAnnotation)
        for record in typed_records:
            buffer.buffer_data(record)
        buffer.flush()
        self._session.commit()
