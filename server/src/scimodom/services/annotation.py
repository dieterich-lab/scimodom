#! /usr/bin/env python3

import os
import logging

# import scimodom.utils.utils as utils
# import scimodom.utils.specifications as specs
# import scimodom.database.queries as queries
import scimodom.database.queries as queries

from typing import ClassVar

# from typing import TypeVar, Type
from sqlalchemy import select

from pathlib import Path


from sqlalchemy.orm import Session

from scimodom.database.models import (
    Data,
    Dataset,
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
    GenomicRegion,
)

# from scimodom.services.importer import EUFImporter
# from scimodom.database.models import (
# Data,
# Dataset,
# Association,
# Selection,
# Modomics,
# Modification,
# DetectionTechnology,
# Organism,
# Assembly,
# )

# T = TypeVar('T', bound='Parent')

logger = logging.getLogger(__name__)


class AnnotationService:
    """Utility class to annotate a dataset.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param eufid: EUFID
    :type eufid: str
    :param DATA_PATH: Path to annotation file
    :type DATA_PATH: str | Path | None
    """

    DATA_PATH: ClassVar[str | Path | None] = os.getenv("DATA_PATH")

    def __init__(self, session: Session, eufid: str) -> None:
        """Initializer method."""
        self._session = session
        self._eufid = eufid

        query = queries.query_column_where(
            Dataset,
            "taxa_id",
            filters={"id": self._eufid},
        )
        self._taxa_id: int = self._session.execute(query).scalar()

        query = queries.get_assembly_version()
        db_assembly_version = session.execute(query).scalar()
        query = queries.query_column_where(
            "Assembly",
            "name",
            filters={"taxa_id": self._taxa_id, "version": db_assembly_version},
        )
        self._assembly: str = self._session.execute(query).scalar()

        query = queries.get_annotation_version()
        db_annotation_version = session.execute(query).scalar()
        query = queries.query_column_where(
            Annotation,
            "release",
            filters={"taxa_id": self._taxa_id, "version": db_annotation_version},
        )
        self._release: int = self._session.execute(query).scalar()

        query = queries.query_column_where(
            Annotation,
            "id",
            filters={
                "taxa_id": self._taxa_id,
                "release": self._release,
                "version": db_annotation_version,
            },
        )
        self._annotation_id: int = self._session.execute(query).scalar()

    def __new__(cls, session: Session, eufid: str):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        else:
            return super(AnnotationService, cls).__new__(cls)

    @classmethod
    def from_new(
        cls,
        session: Session,
        eufid: str,
        fmt: str = "gtf",
    ):
        """Provides AnnotationService factory for first
        time annotation.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param eufid: EUFID
        :type eufid: string
        :param fmt: Annotation file format
        :type fmt: string
        :returns: AnnotationService class instance
        :rtype: AnnotationService
        """
        service = cls(session, eufid)
        service.create_annotation(
            session,
            service._taxa_id,
            service._release,
            service._assembly,
            service.DATA_PATH,
            fmt,
        )
        return service

    @staticmethod
    def create_annotation(
        session: Session,
        taxonomy_id: int,
        release: int,
        assembly: str,
        data_path: str | Path | None,
        fmt: str = "gtf",
    ) -> None:
        """Create destination and download gene annotation.

        NOTE: 06.12.2023 GTF only!
        See scimodom.utils.operations.get_genomic_annotation

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param taxonomy_id: Taxonomy ID for organism
        :type taxonomy_id: integer
        :param release: Release number
        :type release: int
        :param assembly: Assembly
        :type assembly: str
        :param data_path: Path to annotation file
        :type data_path: str | Path | None
        :param fmt: Annotation file format
        :type fmt: str
        """
        import gzip
        import zlib
        import requests  # type: ignore

        import scimodom.utils.specifications as specs

        from sqlalchemy import insert

        from posixpath import join as urljoin
        from scimodom.utils.models import records_factory
        from scimodom.utils.operations import get_genomic_annotation

        if data_path is None or not Path(data_path).is_dir():
            try:
                data_path = os.environ["DATA_PATH"]
            except KeyError:
                msg = "Missing or invalid data path to create annotation. Terminating!"
                logger.error(msg)
                raise

        try:
            query = queries.query_column_where(
                "Taxa",
                "name",
                filters={"id": taxonomy_id},
            )
            organism = session.execute(query).one()
        except:
            msg = f"Organism with taxonomy id {taxonomy_id} not found! Terminating!"
            logger.error(msg)
            return
        organism = "_".join(organism[0].split())

        query = queries.query_column_where(
            Annotation, "release", filters={"taxa_id": taxonomy_id}
        )
        annotation_releases = session.execute(query).scalars().all()
        if release not in annotation_releases:
            msg = f"Given annotation release {release} with taxonomy id {taxonomy_id} not found! Terminating!"
            logger.error(msg)
            return

        query = queries.query_column_where(
            "Assembly", "name", filters={"taxa_id": taxonomy_id}
        )
        assembly_names = session.execute(query).scalars().all()
        if assembly not in assembly_names:
            msg = f"Given assembly {assembly} with taxonomy id {taxonomy_id} not found! Terminating!"
            logger.error(msg)
            return

        msg = "Downloading annotation: this could take a few seconds..."
        logger.debug(msg)

        annotation_file = f"{organism}.{assembly}.{release}.chr.{fmt}.gz"
        try:
            parent = Path(data_path, organism, assembly, str(release))
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            msg = f"Annotation directory at {parent} already exists... continuing!"
            logger.warning(msg)
            parent.mkdir(parents=True, exist_ok=True)
        destination = Path(parent, annotation_file)

        def decompress_stream(stream):
            o = zlib.decompressobj(16 + zlib.MAX_WBITS)
            for chunk in stream:
                yield o.decompress(chunk)
            yield o.flush()

        url = urljoin(
            specs.ANNOTATION_URL,
            f"release-{release}",
            fmt,
            organism.lower(),
            annotation_file,
        )
        with requests.get(url, stream=True) as request:
            if request.ok:
                try:
                    with gzip.open(destination, mode="xb") as filen:
                        for chunk in decompress_stream(
                            request.iter_content(chunk_size=10 * 1024)
                        ):
                            filen.write(chunk)
                except FileExistsError:
                    msg = f"File at {destination} exists. Skipping download!"
                    logger.warning(msg)
                    return
            else:
                msg = f"Request failed with {request.status_code}: {request.content}"
                logger.error(msg)
                return

        # records = get_genomic_annotation(destination, annotation_id)
        # records = [records_factory("GenomicAnnotation", r)._asdict() for r in records]

        # query = queries.query_column_where(GenomicAnnotation, "annotation_id")
        # ids = session.execute(query).scalars().all()
        # if annotation_id in ids:
        # msg = (
        # f"GenomicAnnotation already contains records with annotation_id={annotation_id}. "
        # "Skipping DB transaction! If annotation was downloaded successfully, there is a "
        # "risk of data corruption: check your database! Terminating!"
        # )
        # logger.warning(msg)
        # return
        # session.execute(insert(GenomicAnnotation), records)
        # session.commit()

    def annotate_data(self):
        """Annotate Data: add entries to GenomicAnnotation"""

        query = select(
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.id,
            Data.strand,
        ).where(Data.dataset_id == self._eufid)
        records = self._session.execute(query).all()

        # here

        # query = select(
        # GenomicAnnotation.chrom,
        # GenomicAnnotation.start,
        # GenomicAnnotation.end,
        # GenomicAnnotation.gene_name,
        # GenomicAnnotation.annotation_id,
        # GenomicAnnotation.strand,
        # GenomicAnnotation.id,
        # )
        # annotation = self._session.execute(query).all()
