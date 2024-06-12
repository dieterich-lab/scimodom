import fcntl
import logging
from pathlib import Path
from posixpath import join as urljoin
import re
import shutil
from typing import ClassVar, Callable, Literal, get_args

import requests  # type: ignore
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, exists, insert

from scimodom.config import Config
import scimodom.database.queries as queries
from scimodom.database.buffer import InsertBuffer
from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    Assembly,
    AssemblyVersion,
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


# class AnnotationFormatError(Exception):
#     """Exception handling for Annotation format mismatch."""

#     pass


class AnnotationService:
    """Utility class to handle annotations. Class
    instantiation is only possible for existing
    rows in "annotation" for the current database
    version.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param annotation_id: Annotation ID
    :type annotation_id: str | None
    :param taxid: Taxa ID
    :type taxid: int | None
    :param source: Annotation source
    :type source: str | None
    :param DATA_PATH: Path to data
    :type DATA_PATH: str | Path
    :param ANNOTATION_PATH: Subpath to annotation
    :type ANNOTATION_PATH: str
    :param CACHE_PATH: Path to gene cache
    :type CACHE_PATH: Path
    """

    DATA_PATH: ClassVar[str | Path] = Config.DATA_PATH
    ANNOTATION_PATH: ClassVar[str] = "annotation"
    CACHE_PATH: ClassVar[Path] = Path("cache", "gene", "selection")
    SOURCE = Literal["ensembl", "gtrnadb"]

    def __init__(
        self,
        session: Session,
        bedtools_service: BedToolsService,
        modification_service: ModificationService,
        annotation_id: int | None = None,
        taxa_id: int | None = None,
        source: str | None = None,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._bedtools_service = bedtools_service
        self._modification_service = modification_service

        self._annotation: Annotation
        self._release_path: Path
        self._chrom_file: Path

        # service can only be instantiated for current database annotation version
        version = self._session.execute(
            select(AnnotationVersion.version_num)
        ).scalar_one()

        if annotation_id is not None:
            try:
                annotation = self._session.get_one(Annotation, annotation_id)
                if annotation.version != version:
                    raise AnnotationVersionError(
                        f"Invalid annotation version {annotation.version}"
                    )
            except NoResultFound:
                raise InstantiationError(f"Failed to find annotation {annotation_id}")
        else:
            assert source in get_args(
                self.SOURCE
            ), f"Undefined '{source}'. Allowed values are {self.SOURCE}."
            try:
                annotation = self._session.execute(
                    select(Annotation).filter_by(
                        taxa_id=taxa_id, source=source, version=version
                    )
                ).scalar_one()
            except NoResultFound:
                raise InstantiationError(
                    f"Failed to find annotation for taxonomy ID {taxa_id} and source {source}"
                )

        self._annotation = annotation
        self._set_files_path()

    def __new__(cls, session: Session, **kwargs):
        """Constructor method."""
        if cls.DATA_PATH is None:
            msg = "Missing environment variable: DATA_PATH. Terminating!"
            raise ValueError(msg)
        elif not Path(cls.DATA_PATH, cls.ANNOTATION_PATH).is_dir():
            msg = f"DATA PATH {Path(cls.DATA_PATH, cls.ANNOTATION_PATH)} not found! Terminating!"
            raise FileNotFoundError(msg)
        if not Path(cls.DATA_PATH, cls.CACHE_PATH).is_dir():
            msg = (
                f"DATA PATH {Path(cls.DATA_PATH, cls.CACHE_PATH)} not found! Creating!"
            )
            logger.warning(msg)
            Path(cls.DATA_PATH, cls.CACHE_PATH).mkdir(parents=True, mode=0o755)
        return super().__new__(cls)

    @staticmethod
    def get_annotation_path() -> Path:
        """Construct parent path to annotation files.

        :returns: Path to annotation
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.ANNOTATION_PATH)

    @staticmethod
    def get_cache_path() -> Path:
        """Construct path to gene cache (selection).

        :returns: Path to gene cache
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.CACHE_PATH)

    @staticmethod
    def download(url: str, annotation_file: Path) -> None:
        """Download annotation.

        :param url: Annotation file remote URL
        :type url: str
        :param annotation_file: Path where to write file
        :type annotation_file: Path
        """

        logger.info(f"Downloading annotation to {annotation_file.name} ...")

        with requests.get(url, stream=True) as request:
            if not request.ok:
                request.raise_for_status()
            with open(annotation_file, "wb") as fh:
                for chunk in request.iter_content(chunk_size=10 * 1024):
                    fh.write(chunk)

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

    def _set_files_path(self) -> None:
        """Construct file path (annotation and chrom files) for
        the current annotation."""
        organism_name = self._session.execute(
            select(Taxa.name).filter_by(id=self._annotation.taxa_id)
        ).scalar_one()
        organism_name = "_".join(organism_name.lower().split()).capitalize()
        assembly_version = self._session.execute(
            select(AssemblyVersion.version_num)
        ).scalar_one()
        assembly_name = self._session.execute(
            select(Assembly.name).filter_by(
                taxa_id=self._annotation.taxa_id, version=assembly_version
            )
        ).scalar_one()
        path = self.get_annotation_path()
        self._release_path = Path(
            path, organism_name, assembly_name, str(self._annotation.release)
        )
        parent, filen = AssemblyService.get_chrom_path(organism_name, assembly_name)
        self._chrom_file = Path(parent, filen)

    def _release_exists(self) -> bool:
        """If release exists, the first record for the current
        annotation is queried. An Exception is raised if no
        records are found (i.e. the release destination already exists,
        but the database does not contain the expected annotation records),
        else nothing is done (it is assumed that the database has
        been updated).

        :returns: True if destination already exists, else False
        :rtype: bool
        :raises: Exception
        """
        if self._release_path.exists():
            msg = f"Annotation directory {self._release_path} already exists..."
            logger.info(msg)
            first = self._session.execute(
                select(GenomicAnnotation).filter_by(annotation_id=self._annotation.id)
            ).first()
            if first:
                return True
            msg = f"{msg} but failed to find records in GenomicAnnotation for annotation {self._annotation.id}."
            raise Exception(msg)
        return False


class EnsemblAnnotationService(AnnotationService):
    """Utility class to handle Ensembl annotation.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param **kwargs: Keyword arguments to instantiate
    base class with either "annotation_id", or "taxa_id"
    and "source", cf. AnnotationService.
    :type **kwargs: cf. AnnotationService
    :param FMT: Annotation file format
    :type FMT: str
    :param ANNOTATION_FILE: Annotation file name
    :type ANNOTATION_FILE: Callable
    :param FEATURES: Genomic features
    :type FEATURES: dict of {str: dict of {str: str}}
    """

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

    def create_annotation(self) -> None:
        """This method automates the creation of a database annotation:
        it creates the destination, downloads/writes files to disk,
        wrangles and writes annotation to the database.
        """
        if self._release_exists():
            return

        try:
            # create destination and download files
            self._release_path.mkdir(parents=True, exist_ok=False)
            annotation_file, url = self._get_annotation_paths()
            self.download(url, annotation_file)
            # write BED files for genomic features
            self._bedtools_service.ensembl_to_bed_features(
                annotation_file,
                self._chrom_file,
                {k: list(v.keys()) for k, v in self.FEATURES.items()},
            )
            # add genomic annotation to database
            self._update_database(annotation_file)
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(self._release_path)
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
            raise MissingDataError(f"No records found for {eufid}")

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = self._bedtools_service.annotate_data_to_records(
            self._release_path, features, records
        )
        with InsertBuffer[DataAnnotation](self._session) as buffer:
            for record in annotated_records:
                buffer.queue(DataAnnotation(**record.model_dump()))

    def _update_database(self, annotation_file: Path) -> None:
        """Reads annotation file to records and
        insert to GenomicAnnotation.

        :param annotation_file: Annotation file path
        :type annotation_file: Path
        """
        records = self._bedtools_service.get_ensembl_annotation_records(
            annotation_file,
            self._annotation.id,
            self.FEATURES["extended"]["intergenic"],
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))

    def _get_annotation_paths(self) -> tuple[Path, str]:
        """Construct annotation file path and
        target URL.

        :returns: Annotation file path and URL
        :rtype: (Path, str)
        """
        filen = self.ANNOTATION_FILE(
            organism=self._release_path.parent.parent.name,
            assembly=self._release_path.parent.name,
            release=self._annotation.release,
            fmt=self.FMT,
        )
        url = urljoin(
            specs.ENSEMBL_FTP,
            f"release-{self._annotation.release}",
            self.FMT,
            self._release_path.parent.parent.name.lower(),
            filen,
        )
        return Path(self._release_path, filen), url


class GtRNAdbAnnotationService(AnnotationService):
    """Utility class to handle GtRNAdb annotation.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param **kwargs: Keyword arguments to instantiate
    base class with either "annotation_id", or "taxa_id"
    and "source", cf. AnnotationService.
    :type **kwargs: cf. AnnotationService

    :param FMT: Annotation file format
    :type FMT: str
    :param ANNOTATION_FILE: Annotation file name
    :type ANNOTATION_FILE: Callable
    :param FEATURES: Genomic features
    :type FEATURES: dict of {str: dict of {str: str}}
    """

    FMT: ClassVar[str] = "bed"
    ANNOTATION_FILE: ClassVar[Callable] = "{species}-tRNAs.{fmt}".format
    FEATURES: ClassVar[dict[str, dict[str, str]]] = {
        "conventional": {"exon": "Exonic"},
        "extended": {"intron": "Intronic"},
    }

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        super().__init__(session, **kwargs)

        assembly_alt_name = self._session.execute(
            select(Assembly.alt_name).filter_by(name=self._release_path.parent.name)
        ).scalar_one()
        filen = self.ANNOTATION_FILE(
            assembly=assembly_alt_name,
            fmt=self.FMT,
        )
        self._annotation_file: Path = Path(self._release_path, filen)
        filen = self.ANNOTATION_FILE(
            assembly=assembly_alt_name,
            fmt="fa",
        )
        self._sequence_file: Path = Path(self._release_path, filen)

    def create_annotation(self, domain: str, name: str) -> None:
        """This method automates the creation of a database annotation:
        it creates the destination, downloads, wrangles, and writes files to disk,
        and writes annotation to the database.

        NOTE: GtRNAdb has a non-standard nomenclature, neither API nor FTP.
        Prior to calling this method, lookup the remote detination to find the
        correct domain and name, e.g. GTRNADB_URL/domain/name/assembly-tRNAs.fa.
        Choose the assembly that matches the current database assembly. The
        GtRNAdb assembly matches the database assembly "alt_name".

        :param domain: Taxonomic domain e.g. eukaryota
        :type domain: str
        :param name: GtRNAdb species name (abbreviated) e.g. Mmusc39
        :type name: str
        """
        if self._destination_exists():
            return

        try:
            for filen in [self._annotation_file, self._sequence_file]:
                url = urljoin(
                    specs.GTRNADB_URL,
                    domain,
                    name,
                    filen.name,
                )
                self.download(url, filen)
            self._patch_annotation()
        #     # TODO
        #     actually write annotation to BED for exons/introns
        #     and write/flush to database
        #     finally create model mappings
        #     self._session.commit()
        except:
            pass
        #     self._session.rollback()
        #     shutil.rmtree(self._release_path)
        #     raise

    def _patch_annotation(self):
        """Re-write GtRNAdb annotation file according to
        Ensembl format, and filter out contigs/scaffolds.
        """
        pattern = "^chr"
        repl = ""

        seqids = AssemblyService.get_seqids(chrom_file=self._chrom_file)

        with open(self._annotation_file, "r") as fd:
            text, counter = re.subn(pattern, repl, fd.read(), flags=re.MULTILINE)

        if counter != len(text.splitlines()):
            msg = "Chromosome substitution failed: expected one match per line!"
            logger.warning(msg)

        with open(self._annotation_file, "w") as fd:
            for line in text.splitlines():
                if line.split("\t")[0] not in seqids:
                    continue
                fd.write(f"{line}\n")
