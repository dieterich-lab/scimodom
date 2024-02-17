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
from scimodom.database.models import Annotation, Assembly, GenomicAnnotation, Taxa

# from scimodom.utils.models import records_factory
# from scimodom.utils.operations import get_genomic_annotation
import scimodom.utils.specifications as specs

logger = logging.getLogger(__name__)


class AnnotationVersionError(Exception):
    """Exception handling for Annotatoin version mismatch."""

    pass


class AnnotationService:
    """Utility class to handle annotations.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param annotation_id: Annotation ID
    :type annotation_id: str
    :param taxid: Taxa ID
    :type taxid: int
    :param release: Taxa ID
    :type release: int
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

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        self._session = session

        self._annotation_id: int
        self._db_versiob: str
        self._taxid: int
        self._release: int
        self._annotation_file: Path

        # current DB assembly version
        query = queries.get_annotation_version()
        self._db_version = self._session.execute(query).scalar()

        annotation_id = kwargs.get("annotation_id", None)
        taxa_id = kwargs.get("taxa_id", None)
        if annotation_id is not None:
            self._annotation_id = annotation_id
            query = queries.query_column_where(
                Annotation,
                ["release", "taxa_id", "version"],
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
            self._taxid = records["taxa_id"]
            self._release = records["release"]
        elif taxa_id is not None:
            self._taxid = taxa_id
            release = kwargs.get("release", None)
            if release is not None:
                self._release = release
                query = queries.query_column_where(
                    Annotation,
                    "version",
                    filters={"taxa_id": self._taxid, "release": self._release},
                )
                version = self._session.execute(query).scalar_one()
                if not version == self._db_version:
                    pass
                    # TODO do we allow creating a new version?
            else:
                query = queries.query_column_where(
                    Annotation,
                    "release",
                    filters={"taxa_id": self._taxid, "version": self._db_version},
                )
                self._release = self._session.execute(query).scalar_one()
            query = queries.query_column_where(
                Annotation,
                "id",
                filters={
                    "taxa_id": self._taxid,
                    "release": self._release,
                    "version": self._db_version,
                },
            )
            self._annotation_id = self._session.execute(query).scalar_one()

        self._get_annotation_file_path()

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
        and write to database. If the destination already
        exists, the first record for the current annotation
        is queried. If None, this raises a FileExistsError
        (annotation file exists, but the database does not
        appear to have been updated). If not None, nothing
        is done, there is no further check. If the destination
        does not exist, it is created, and the annotation
        is written to the database.
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
            return

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
            with open(self._annotation_file, "wb") as f:
                for chunk in request.iter_content(chunk_size=10 * 1024):
                    f.write(chunk)

        self._create_annotation()

    def _get_annotation_file_path(self) -> None:
        """Construct file path (annotation file) for
        the current annotation."""
        query = queries.query_column_where(Taxa, "name", filters={"id": self._taxid})
        organism_name = self._session.execute(query).scalar_one()
        query = queries.get_assembly_version()
        version = self._session.execute(query).scalar_one()
        query = queries.query_column_where(
            Assembly, "name", filters={"taxa_id": self._taxid, "version": version}
        )
        assembly_name = self._session.execute(query).scalar_one()
        organism_name = "_".join(organism_name.lower().split()).capitalize()
        path = self.get_annotation_path()
        parent = Path(path, organism_name, assembly_name, str(self._release))
        filen = self.ANNOTATION_FILE(
            organism=organism_name,
            assembly=assembly_name,
            release=self._release,
            fmt=self.FMT,
        )
        self._annotation_file = Path(parent, filen)

    def _create_annotation(self) -> None:
        """Reads annotation file to records and
        insert to GenomicAnnotation."""
        pass
        # call operations, this returns all the records
        # find a way to bulk insert (w or w/o buffering, check import buffer maybe)

    def annotate_data(self):
        """Annotate Data: add entries to GenomicAnnotation

        NOTE: 06.12.2023 GTF only!
        See scimodom.utils.operations.get_genomic_annotation

        """
        pass
        # query = select(
        #     Data.chrom,
        #     Data.start,
        #     Data.end,
        #     Data.name,
        #     Data.id,
        #     Data.strand,
        # ).where(Data.dataset_id == self._eufid)
        # records = self._session.execute(query).all()

        # msg = "Annotating records may take a few minutes..."
        # logger.debug(msg)

        # annotated = get_genomic_annotation(
        #     self._annotation_file, self._chrom_file, self._annotation_id, records
        # )

        # msg = "... done! Now inserting into DB."
        # logger.debug(msg)

        # TODO
        # annotated = [
        #     records_factory("GenomicAnnotation", r)._asdict() for r in annotated
        # ]
        # self._session.execute(insert(GenomicAnnotation), annotated)
        # self._session.commit()
