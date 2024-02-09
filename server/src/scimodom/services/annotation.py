#! /usr/bin/env python3

import gzip
import logging
import os
from pathlib import Path
from posixpath import join as urljoin
from typing import ClassVar
import zlib

import requests  # type: ignore
from sqlalchemy import select, insert
from sqlalchemy.orm import Session

from scimodom.config import Config
import scimodom.database.queries as queries
from scimodom.database.models import (
    Data,
    Dataset,
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
)
from scimodom.utils.models import records_factory
from scimodom.utils.operations import get_genomic_annotation
import scimodom.utils.specifications as specs

# T = TypeVar('T', bound='Parent')

logger = logging.getLogger(__name__)


class AnnotationService:
    """Utility class to annotate a dataset.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param eufid: EUFID
    :type eufid: str
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
    FMT: ClassVar[str] = "gtf"  # 12.23 only handle GTF

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        self._session = session
        self._eufid: str
        self._taxa_id: int

        eufid = kwargs.get("eufid", None)
        taxa_id = kwargs.get("taxid", None)
        if eufid is not None:
            self._eufid = eufid
            query = queries.query_column_where(
                Dataset,
                "taxa_id",
                filters={"id": self._eufid},
            )
            self._taxa_id = self._session.execute(query).scalar()
        else:
            # TODO validate if not None/or type
            self._taxa_id = taxa_id

        query = queries.get_assembly_version()
        db_assembly_version = self._session.execute(query).scalar()
        query = queries.query_column_where(
            "Assembly",
            "name",
            filters={"taxa_id": self._taxa_id, "version": db_assembly_version},
        )
        self._assembly: str = self._session.execute(query).scalar()

        query = queries.get_annotation_version()
        db_annotation_version = self._session.execute(query).scalar()
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

        query = queries.query_column_where(
            "Taxa",
            "name",
            filters={"id": self._taxa_id},
        )
        organism = self._session.execute(query).scalar()
        organism = "_".join(organism.split())

        parent, filen = self.get_annotation_path(
            Path(self.DATA_PATH, self.DATA_SUB_PATH),
            organism,
            self._assembly,
            self._release,
            self.FMT,
        )
        self._annotation_file: Path = Path(parent, filen)
        parent, filen = self.get_chrom_path(
            Path(self.DATA_PATH, self.DATA_SUB_PATH), organism, self._assembly
        )
        self._chrom_file: Path = Path(parent, filen)

    def __new__(cls, session: Session, **kwargs):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.DATA_SUB_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.DATA_SUB_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        else:
            # TODO
            # if not all(key in ["eufid", "taxid"] for key in kwargs):
            #     msg = "Missing keyword argument eufid or taxid to class! Terminating!"
            #     raise ValueError(msg)
            return super(AnnotationService, cls).__new__(cls)

    @classmethod
    def from_new(cls, session: Session, eufid: str):
        """Provides AnnotationService factory for first
        time annotation from EUFID.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param eufid: EUFID
        :type eufid: string
        :returns: AnnotationService class instance
        :rtype: AnnotationService
        """
        service = cls(session, eufid=eufid)
        service.create_annotation(
            session,
            service._taxa_id,
            service._release,
            service._assembly,
            Path(service.DATA_PATH, service.DATA_SUB_PATH),
            service.FMT,
        )
        return service

    @classmethod
    def from_taxid(cls, session: Session, taxid: int):
        """Provides AnnotationService factory for first
        time annotation from taxa ID.

        :param session: SQLAlchemy ORM session
        :type session: Session
        :param taxid: Taxa ID
        :type taxid: int
        :returns: AnnotationService class instance
        :rtype: AnnotationService
        """
        service = cls(session, taxid=taxid)
        service.create_annotation(
            session,
            service._taxa_id,
            service._release,
            service._assembly,
            Path(service.DATA_PATH, service.DATA_SUB_PATH),
            service.FMT,
        )
        return service

    @staticmethod
    def get_annotation_path(
        path: str | Path | None, organism: str, assembly: str, release: int, fmt: str
    ) -> tuple[Path, str]:
        """Construct file path (annotation)

        :param path: Base path
        :type path: str | Path
        :param organism: Organism
        :type organism: str
        :param assembly: Assembly
        :type assembly: str
        :param release: Annotation release
        :type release: int
        :param fmt: Annotation file format
        :type fmt: str
        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        if path is None:
            raise TypeError(
                "Missing DATA PATH! Cannot construct path to annotation file!"
            )
        parent = Path(path, organism, assembly, str(release))
        filen = f"{organism}.{assembly}.{release}.chr.{fmt}.gz"
        return parent, filen

    @staticmethod
    def get_chrom_path(
        path: str | Path | None, organism: str, assembly: str
    ) -> tuple[Path, str]:
        """Construct file path (chrom sizes)

        :param path: Base path
        :type path: str | Path
        :param organism: Organism
        :type organism: str
        :param assembly: Assembly
        :type assembly: str
        :returns: Parent and file name
        :rtype: tuple[str | Path, str]
        """
        if path is None:
            raise TypeError("Missing DATA PATH! Cannot construct path to chrom.sizes!")
        parent = Path(path, organism, assembly)
        return parent, "chrom.sizes"

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

        # from scimodom.utils.operations import get_genomic_annotation

        if data_path is None or not Path(data_path).is_dir():
            try:
                data_path = Path(
                    os.environ["DATA_PATH"], AnnotationService.DATA_SUB_PATH
                )
            except KeyError:
                msg = "Missing or invalid DATA PATH to create annotation. Terminating!"
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

        parent, annotation_file = AnnotationService.get_annotation_path(
            data_path, organism, assembly, release, fmt
        )
        try:
            parent.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            msg = f"Annotation directory at {parent} already exists... continuing!"
            logger.warning(msg)
            parent.mkdir(parents=True, exist_ok=True)
        annotation_path = Path(parent, annotation_file)

        # TODO check assembly...
        def decompress_stream(stream):
            o = zlib.decompressobj(16 + zlib.MAX_WBITS)
            for chunk in stream:
                yield o.decompress(chunk)
            yield o.flush()

        url = urljoin(
            specs.ENSEMBL_FTP,
            f"release-{release}",
            fmt,
            organism.lower(),
            annotation_file,
        )
        with requests.get(url, stream=True) as request:
            if not request.ok:
                request.raise_for_status()
            try:
                with gzip.open(annotation_path, mode="xb") as afile:
                    for chunk in decompress_stream(
                        request.iter_content(chunk_size=10 * 1024)
                    ):
                        afile.write(chunk)
            except FileExistsError:
                msg = f"File at {annotation_path} exists. Skipping!"
                logger.warning(msg)

        # here now, but may be moved to assembly service...
        # here parent is one dir up, assume it exists (see above)...
        # overvrite
        parent, chrom_file = AnnotationService.get_chrom_path(
            data_path, organism, assembly
        )
        chrom_path = Path(parent, chrom_file)

        url = urljoin(
            specs.ENSEMBL_SERVER,
            specs.ENSEMBL_ASM,
            organism.lower(),
        )
        request = requests.get(url, headers={"Content-Type": "application/json"})
        if not request.ok:
            request.raise_for_status()
        gene_build = request.json()
        coord_sysver = gene_build["default_coord_system_version"]
        if not coord_sysver == assembly:
            msg = (
                f"Mismatch between assembly {assembly} and current coord system version {coord_sysver}! "
                "Upgrade your database! Continuing anyway..."
            )
            logger.warning(msg)
            if assembly not in gene_build["coord_system_versions"]:
                msg = f"Assembly {assembly} not in available coord system versions! Terminating!"
                raise ValueError(msg)

        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] == "chromosome" and d["name"] in chroms
        }
        try:
            with open(chrom_path, "x") as cfile:
                for chrom in sorted(chroms):
                    cfile.write(f"{chrom}\t{top_level[chrom]}\n")
        except FileExistsError:
            msg = f"File at {chrom_path} exists. Skipping!"
            logger.warning(msg)

    def annotate_data(self):
        """Annotate Data: add entries to GenomicAnnotation

        NOTE: 06.12.2023 GTF only!
        See scimodom.utils.operations.get_genomic_annotation

        """

        query = select(
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.id,
            Data.strand,
        ).where(Data.dataset_id == self._eufid)
        records = self._session.execute(query).all()

        msg = "Annotating records may take a few minutes..."
        logger.debug(msg)

        annotated = get_genomic_annotation(
            self._annotation_file, self._chrom_file, self._annotation_id, records
        )

        msg = "... done! Now inserting into DB."
        logger.debug(msg)

        # TODO
        # annotated = [
        #     records_factory("GenomicAnnotation", r)._asdict() for r in annotated
        # ]
        # self._session.execute(insert(GenomicAnnotation), annotated)
        # self._session.commit()
