#! /usr/bin/env python3

import os
import logging

# import scimodom.utils.utils as utils
# import scimodom.utils.specifications as specs
# import scimodom.database.queries as queries

from typing import ClassVar

# from typing import TypeVar, Type
# from sqlalchemy import select, func

from pathlib import Path


from sqlalchemy.orm import Session

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
    """

    DATA_PATH: ClassVar[str | Path | None] = os.getenv("DATA_PATH")

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def __new__(cls, session: Session):
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        else:
            return super(AnnotationService, cls).__new__(cls)

    @classmethod
    def from_new(
        cls,
        session: Session,
        taxonomy_id: int,
        release: int,
        assembly: str | None = None,
        fmt: str = "gtf",
    ):
        """Provides AnnotationService factory for first
        time annotation.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param taxonomy_id: Taxonomy ID for organism
        :type taxonomy_id: integer
        :param release: Release number
        :type release: integer
        :param assembly: Assembly
        :type assembly: string | None
        :param fmt: Annotation file format
        :type fmt: string
        :returns: AnnotationService class instance
        :rtype: AnnotationService
        """
        service = cls(session)
        service.create_annotation(
            session, service.DATA_PATH, taxonomy_id, release, assembly, fmt
        )
        return service

    @staticmethod
    def create_annotation(
        session: Session,
        data_path: str | Path | None,
        taxonomy_id: int,
        release: int | None = None,
        assembly: str | None = None,
        fmt: str = "gtf",
    ) -> None:
        """Download and wrangle gene annotation.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param taxonomy_id: Taxonomy ID for organism
        :type taxonomy_id: integer
        :param release: Release number
        :type release: integer | None
        :param assembly: Assembly
        :type assembly: string | None
        :param fmt: Annotation file format
        :type fmt: string
        """
        import gzip
        import zlib
        import requests  # type: ignore

        import scimodom.utils.specifications as specs
        import scimodom.database.queries as queries

        from posixpath import join as urljoin
        from scimodom.utils.operations import get_genomic_annotation

        if data_path is None:
            msg = "Missing data path. Terminating!"
            raise ValueError(msg)

        try:
            query = queries.query_column_where(
                "Taxa",
                "name",
                filters={"id": taxonomy_id},
            )
            organism = session.execute(query).one()
        except:
            msg = f"Organism with taxonomy id={taxonomy_id} not found! Terminating!"
            logger.error(msg)
            return
        organism = "_".join(organism[0].split())

        if release is None:
            query = queries.get_annotation_version()
            db_annotation_version = session.execute(query).scalar()
            query = queries.query_column_where(
                "Annotation",
                "release",
                filters={"taxa_id": taxonomy_id, "version": db_annotation_version},
            )
            release = session.execute(query).scalar()
        else:
            query = queries.query_column_where(
                "Annotation", "release", filters={"taxa_id": taxonomy_id}
            )
            annotation_releases = session.execute(query).scalars().all()
            if release not in annotation_releases:
                msg = f"Given annotation release={release} with taxonomy id={taxonomy_id} not found! Terminating!"
                logger.error(msg)
                return
        query = queries.query_column_where(
            "Annotation",
            "id",
            filters={
                "taxa_id": taxonomy_id,
                "release": release,
                "version": db_annotation_version,
            },
        )
        annotation_id = session.execute(query).scalar()

        if assembly is None:
            query = queries.get_assembly_version()
            db_assembly_version = session.execute(query).scalar()
            query = queries.query_column_where(
                "Assembly",
                "name",
                filters={"taxa_id": taxonomy_id, "version": db_assembly_version},
            )
            assembly = session.execute(query).scalar()
        else:
            query = queries.query_column_where(
                "Assembly", "name", filters={"taxa_id": taxonomy_id}
            )
            assembly_names = session.execute(query).scalars().all()
            if assembly not in assembly_names:
                msg = f"Given assembly={assembly} with taxonomy id={taxonomy_id} not found! Terminating!"
                logger.error(msg)
                return

        annotation_file = f"{organism}.{assembly}.{release}.chr.{fmt}.gz"
        destination = Path(data_path, annotation_file)

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
                with gzip.open(destination, mode="xb") as filen:
                    for chunk in decompress_stream(
                        request.iter_content(chunk_size=10 * 1024)
                    ):
                        filen.write(chunk)
            else:
                msg = f"Request failed with {request.status_code}. Content: {request.content}"
                logger.error(msg)
                return

        records = get_genomic_annotation(destination, annotation_id)
        # convet records to dict for bulk insert - where are models now? -> generalize

        # need a warning/error before commit if entries exists already, check for annotation_id?
        # bulk insert

        # can pybedtool/bedtool work with gzip data? YES do not uncompress
        # TODO:
        # 1. sort gtf
        # 2. extract exons, UTRS, CDS, and genes for processing
        # 3. subtract exons from genes -> introns
        # 4. complement genes (we need chrom sizes) -> intergenic
        # ? Do we work in some tmp directory, and move relevant files when done (context manager - rm all remaining files? incl. bedtools?)

        # create class method to use or not create_annotation
