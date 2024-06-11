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
from scimodom.services.importer import get_buffer
from scimodom.services.importer.base import MissingDataError
from scimodom.utils.operations import (
    write_annotation_to_bed,
    get_annotation_records,
    annotate_data_to_records,
)
from scimodom.utils.models import records_factory
import scimodom.utils.specifications as specs

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
    """Utility class to handle annotations. Class
    instantiation is only possible for existing
    rows in "annotation".

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
        annotation_id: int | None = None,
        taxa_id: int | None = None,
        source: str | None = None,
    ) -> None:
        """Initializer method."""
        self._session = session

        self._annotation: Annotation
        self._release_path: Path
        self._chrom_file: Path

        if annotation_id is not None:
            try:
                annotation = self._session.get_one(Annotation, annotation_id)
            except NoResultFound:
                raise InstantiationError(f"Failed to find annotation {annotation_id}")
        else:
            assert source in get_args(
                self.SOURCE
            ), f"Undefined '{source}'. Allowed values are {self.SOURCE}."
            try:
                annotation = self._session.execute(
                    select(Annotation).filter_by(taxa_id=taxa_id, source=source)
                ).scalar_one()
            except NoResultFound:
                raise InstantiationError(
                    f"Failed to find annotation with taxonomy ID {taxa_id} and source {source}"
                )

        # service can only be instantiated for current database annotation version
        version = self._session.execute(
            select(AnnotationVersion.version_num)
        ).scalar_one()
        if not annotation.version == version:
            raise AnnotationVersionError(
                f"Invalid annotation version {annotation.version}"
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
        else:
            if not Path(cls.DATA_PATH, cls.CACHE_PATH).is_dir():
                msg = f"DATA PATH {Path(cls.DATA_PATH, cls.CACHE_PATH)} not found! Creating!"
                logger.warning(msg)
                Path(cls.DATA_PATH, cls.CACHE_PATH).mkdir(parents=True, mode=0o755)
            return super(AnnotationService, cls).__new__(cls)

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

    def _destination_exists(self) -> bool:
        """Creates destination if it does not already exists.
        If destination exists, the first record for the current
        annotation is queried. A FileExistsError is raised if no
        records are found (i.e. the destination already exists, but
        the database does not contain the expected annotation records),
        else nothing is done (it is assumed that the database has
        been updated).

        :returns: True if destination already exists, else False (and
        destination is created)
        :rtype: bool
        :raises: Exception from FileExistsError
        """
        try:
            self._release_path.mkdir(parents=True, exist_ok=False)
            return False
        except FileExistsError as exc:
            msg = f"Annotation directory {self._release_path} already exists..."
            logger.info(msg)
            first = self._session.execute(
                select(GenomicAnnotation).filter_by(annotation_id=self._annotation.id)
            ).first()
            if first:
                return True
            msg = f"{msg} but failed to find records in GenomicAnnotation for annotation {self._annotation.id}."
            raise Exception(msg) from exc


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

    def __init__(self, session: Session, **kwargs) -> None:
        """Initializer method."""
        super().__init__(session, **kwargs)

        filen = self.ANNOTATION_FILE(
            organism=self._release_path.parent.parent.name,
            assembly=self._release_path.parent.name,
            release=self._annotation.release,
            fmt=self.FMT,
        )
        self._annotation_file: Path = Path(self._release_path, filen)

    def create_annotation(self) -> None:
        """This method automates the creation of a database annotation:
        it creates the destination, downloads/writes files to disk,
        wrangles and writes annotation to the database.
        """
        if self._destination_exists():
            return

        try:
            url = urljoin(
                specs.ENSEMBL_FTP,
                f"release-{self._annotation.release}",
                self.FMT,
                self._release_path.parent.parent.name.lower(),
                self._annotation_file.name,
            )
            self.download(url, self._annotation_file)
            features = {k: list(v.keys()) for k, v in self.FEATURES.items()}
            # TODO
            write_annotation_to_bed(
                self._annotation_file, self._chrom_file, features, AnnotationFormatError
            )
            # TODO
            self._create_annotation()
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(self._release_path)
            raise

    # TODO
    def annotate_data(self, eufid: str) -> None:
        """Annotate Data: add entries to DataAnnotation
        for a given dataset.

        :param eufid: EUF ID
        :type eufid: str
        """
        query = select(
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.score,
            Data.strand,
            Data.id,
        ).where(Data.dataset_id == eufid)
        records = self._session.execute(query).all()

        if len(records) == 0:
            msg = f"[Annotation] No records found for {eufid}... "
            raise MissingDataError(msg)

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
        self._session.flush()

    # TODO
    def _create_annotation(self) -> None:
        """Reads annotation file to records and
        insert to GenomicAnnotation."""
        records = get_annotation_records(
            self._annotation_file,
            self._annotation.id,
            self.FEATURES["extended"]["intergenic"],
        )
        typed_records = [
            records_factory("GenomicAnnotation", r)._asdict() for r in records
        ]
        buffer = get_buffer(GenomicAnnotation)
        for record in typed_records:
            buffer.buffer_data(record)
        buffer.flush()


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
