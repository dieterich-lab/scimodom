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

    DATA_PATH: ClassVar[str | Path] = os.getenv("DATA_PATH")

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    @staticmethod
    def create_annotation(
        session: Session,
        data_path: str | Path,
        taxonomy_id: int,
        release: int,
        assembly: str | None = None,
        fmt: str = "gff3",
    ) -> None:
        """Download and wrangle gene annotation.

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
        """
        import gzip
        import zlib
        import requests

        import scimodom.utils.specifications as specs

        import scimodom.database.queries as queries

        from posixpath import join as urljoin

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
                msg = f"Given assembly {assembly} with taxonomy id={taxonomy_id} not found! Terminating!"
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

        # can pybedtool/bedtool work with gzip data? YES do not uncompress
        # TODO:
        # 1. sort gtf
        # 2. extract exons, UTRS, CDS, and genes for processing
        # 3. subtract exons from genes -> introns
        # 4. complement genes (we need chrom sizes) -> intergenic
        # ? Do we work in some tmp directory, and move relevant files when done (context manager - rm all remaining files? incl. bedtools?)

        # create class method to use or not create_annotation
