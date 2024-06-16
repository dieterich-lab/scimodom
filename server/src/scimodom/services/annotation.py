from functools import cache
import fcntl
import logging
from pathlib import Path
from posixpath import join as urljoin
import re
import shutil
from typing import ClassVar, Callable, NamedTuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from sqlalchemy import select, func

from scimodom.config import Config
from scimodom.database.buffer import InsertBuffer
from scimodom.database.database import get_session
from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    Assembly,
    Data,
    DataAnnotation,
    GenomicAnnotation,
    Taxa,
)
from scimodom.services.assembly import get_assembly_service, AssemblyService
from scimodom.services.data import get_data_service, DataService
from scimodom.services.external import get_external_service, ExternalService
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
import scimodom.utils.specifications as specs
from scimodom.utils.utils import stream_request_to_file

logger = logging.getLogger(__name__)


class AnnotationNotFoundError(Exception):
    """Exception handling for a non-existing Annotation
    or Annotation that is not the latest version."""

    pass


class AnnotationService:
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

    def __init__(
        self,
        session: Session,
        assembly_service: AssemblyService,
        data_service: DataService,
        bedtools_service: BedToolsService,
        external_service: ExternalService,
    ) -> None:
        """Initializer method."""
        self._session = session
        self._assembly_service = assembly_service
        self._data_service = data_service
        self._bedtools_service = bedtools_service
        self._external_service = external_service

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
        return Path(AnnotationService.DATA_PATH, AnnotationService.ANNOTATION_PATH)

    @staticmethod
    def get_cache_path() -> Path:
        """Construct path to gene cache (selection).

        :returns: Path to gene cache
        :rtype: Path
        """
        return Path(AnnotationService.DATA_PATH, AnnotationService.CACHE_PATH)

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


class EnsemblAnnotationService(AnnotationService):
    """Utility class to handle Ensembl annotation.

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

    def get_annotation(self, taxa_id: int) -> Annotation:
        """Retrieve annotation from taxonomy ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        return self.get_annotation_from_taxid_and_source(taxa_id, "ensembl")

    def create_annotation(self, taxa_id: int) -> None:
        """This method automates the creation of Ensembl
        annotations for a given organism for the current
        release. The annotation must exists in the database.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        """
        annotation = self.get_annotation(taxa_id)
        if self._release_exists(annotation.id):
            return

        release_path = self.get_release_path(annotation)
        annotation_file, url = self._get_annotation_paths(annotation, release_path)
        chrom_file = self._assembly_service.get_chrom_file(annotation.taxa_id)

        logger.info(
            f"Setting up Ensembl {annotation.release} for {annotation.taxa_id}..."
        )

        try:
            release_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            exc.add_note(f"... but no records found for annotation {annotation.id}.")
            raise

        try:
            stream_request_to_file(url, annotation_file)
            self._bedtools_service.ensembl_to_bed_features(
                annotation_file,
                chrom_file,
                {k: list(v.keys()) for k, v in self.FEATURES.items()},
            )
            self._update_database(annotation.id, annotation_file)
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(release_path)
            raise

    def annotate_data(self, taxa_id: int, eufid: str) -> None:
        """Annotate Data: add entries to DataAnnotation
        for a given dataset.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param eufid: EUF ID
        :type eufid: str
        """
        annotation = self.get_annotation(taxa_id)
        release_path = self.get_release_path(annotation)

        logger.debug(f"Annotating records for EUFID {eufid}...")

        records = list(self._data_service.get_by_dataset(eufid))

        features = {**self.FEATURES["conventional"], **self.FEATURES["extended"]}
        annotated_records = self._bedtools_service.annotate_data_using_ensembl(
            release_path, features, records
        )
        with InsertBuffer[DataAnnotation](self._session) as buffer:
            for record in annotated_records:
                buffer.queue(DataAnnotation(**record.model_dump()))

    def _update_database(self, annotation_id: int, annotation_file: Path) -> None:
        records = self._bedtools_service.get_ensembl_annotation_records(
            annotation_file,
            annotation_id,
            self.FEATURES["extended"]["intergenic"],
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))

    def _get_annotation_paths(
        self, annotation: Annotation, release_path: Path
    ) -> tuple[Path, str]:
        filen = self.ANNOTATION_FILE(
            organism=release_path.parent.parent.name,
            assembly=release_path.parent.name,
            release=annotation.release,
            fmt=self.FMT,
        )
        url = urljoin(
            specs.ENSEMBL_FTP,
            f"release-{annotation.release}",
            self.FMT,
            release_path.parent.parent.name.lower(),
            filen,
        )
        return Path(release_path, filen), url


class GtRNAdbAnnotationService(AnnotationService):
    """Utility class to handle GtRNAdb annotation.

    :param FMT: Annotation format. BED is used for
    annotations (GTF is no available for all organisms),
    and FASTA for coordinates mapping.
    :type FMT: list of str
    :param ANNOTATION_FILE: Annotation file pattern
    :type ANNOTATION_FILE: Callable
    :param FEATURES: Genomic features
    :type FEATURES: dict of {str: str}
    """

    FMT: ClassVar[list[str]] = ["bed", "fa"]
    ANNOTATION_FILE: ClassVar[Callable] = "{species}-tRNAs.{fmt}".format
    FEATURES: ClassVar[dict[str, str]] = {"exon": "Exonic", "intron": "Intronic"}

    AnnotationPath: NamedTuple = NamedTuple(
        "AnnotationPath", [("annotation_file", Path), ("url", str)]
    )

    def get_annotation(self, taxa_id: int) -> Annotation:
        """Retrieve annotation from taxonomy ID.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :returns: Annotation instance
        :rtype: Annotation

        :raises: AnnotationNotFoundError
        """
        return self.get_annotation_from_taxid_and_source(taxa_id, "gtrnadb")

    def create_annotation(self, taxa_id: int, domain: str, name: str) -> None:
        """This method automates the creation of GtRNAdb
        annotations for a given organism. The annotation
        must exists in the database.

        NOTE: Prior to calling this method, lookup the remote
        detination to find the correct domain and name, e.g.
        GTRNADB_URL/domain/name/assembly-tRNAs.fa. Choose the
        assembly that matches the current database assembly.

        :param taxa_id: Taxonomy ID
        :type taxa_id: int
        :param domain: Taxonomic domain e.g. eukaryota
        :type domain: str
        :param name: GtRNAdb species name (abbreviated) e.g. Mmusc39
        :type name: str
        """
        annotation = self.get_annotation(taxa_id)
        if self._release_exists(annotation.id):
            return

        release_path = self.get_release_path(annotation)
        annotation_paths = self._get_annotation_paths(release_path, domain, name)
        annotation_file = annotation_paths["bed"].annotation_file
        fasta_file = annotation_paths["fa"].annotation_file
        seqids = self._assembly_service.get_seqids(annotation.taxa_id)

        logger.info(
            f"Setting up GtRNAdb {annotation.release} for {annotation.taxa_id}..."
        )

        try:
            release_path.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            exc.add_note(f"... but no records found for annotation {annotation.id}.")
            raise

        try:
            for paths in annotation_paths.values():
                stream_request_to_file(paths.url, paths.annotation_file)
            self._bedtools_service.gtrnadb_to_bed_features(
                annotation_file, list(self.FEATURES.keys())
            )
            # TODO
            # self._update_annotation()
            self._update_database(
                annotation_file, annotation.id, release_path.parent.parent.name
            )
            self._session.commit()
        except:
            self._session.rollback()
            shutil.rmtree(release_path)
            raise

    def _get_annotation_paths(
        self, release_path: Path, domain: str, name: str
    ) -> dict[AnnotationPath]:
        assembly_alt_name = self._session.execute(
            select(Assembly.alt_name).filter_by(name=release_path.parent.name)
        ).scalar_one()
        paths = {}
        for fmt in self.FMT:
            filen = self.ANNOTATION_FILE(
                assembly=assembly_alt_name,
                fmt=fmt,
            )
            url = urljoin(
                specs.GTRNADB_URL,
                domain,
                name,
                filen,
            )
            paths[fmt] = self.AnnotationPath(Path(release_path, filen), url)
        return paths

    def _patch_annotation(self, annotation_file: Path, seqids: list[str]):
        # TODO Is it general enough to handle all organisms?
        # TODO restrict to highly confident set...

        pattern = "^chr"
        repl = ""
        with open(annotation_file, "r") as fd:
            text, counter = re.subn(pattern, repl, fd.read(), flags=re.MULTILINE)

        if counter != len(text.splitlines()):
            logger.warning(
                "Chromosome substitution may have failed: expected one match per line!"
            )

        with open(annotation_file, "w") as fd:
            for line in text.splitlines():
                if line.split("\t")[0] not in seqids:
                    continue
                fd.write(f"{line}\n")

    # TODO
    def _update_annotation(self, domain, fasta_file):
        annotation_path = self.get_annotation_path()
        model_file = Path(annotation_path, domain).with_suffix(".cm").as_posix()
        sprinzl_file = Path(annotation_path, domain).with_suffix(".txt").as_posix()
        self._external_service.get_sprinzl_mapping(model_file, fasta_file, sprinzl_file)

        # self._patch_annotation(annotation_file, seqids)

        # maybe we need to patch the annotation here
        # restrict to highly confident set
        # patch
        # and at the same time update mapping file with chrom start

    def _update_database(
        self, annotation_file: Path, annotation_id: int, organism: str
    ) -> None:
        records = self._bedtools_service.get_gtrnadb_annotation_records(
            annotation_file,
            annotation_id,
            organism,
        )
        with InsertBuffer[GenomicAnnotation](self._session) as buffer:
            for record in records:
                buffer.queue(GenomicAnnotation(**record.model_dump()))


@cache
def get_annotation_service(source: str) -> AnnotationService:
    """Helper function to set up an AnnotationService object by injecting its dependencies.

    :param source: Ensembl or GtRNAdb annotation
    :type source: str
    :returns: Annotation service instance
    :rtype: AnnotationService
    """
    if source == "ensembl":
        return EnsemblAnnotationService(
            session=get_session(),
            assembly_service=get_assembly_service(),
            data_service=get_data_service(),
            bedtools_service=get_bedtools_service(),
            external_service=get_external_service(),
        )
    elif source == "gtrnadb":
        return GtRNAdbAnnotationService(
            session=get_session(),
            assembly_service=get_assembly_service(),
            data_service=get_data_service(),
            bedtools_service=get_bedtools_service(),
            external_service=get_external_service(),
        )
    else:
        raise ValueError(f"No such annotation: '{source}'.")
