import logging
import gzip
import os
import re
from contextlib import contextmanager
from fcntl import flock, LOCK_SH, LOCK_EX, LOCK_UN, LOCK_NB, lockf
from functools import cache
from os import unlink, rename, makedirs, stat, close, umask, replace
from os.path import join, exists, dirname, basename, isfile
from pathlib import Path
from shutil import copyfileobj, rmtree
from tempfile import mkstemp, NamedTemporaryFile
from typing import (
    Optional,
    IO,
    List,
    Dict,
    TextIO,
    BinaryIO,
    Iterable,
    Any,
    ClassVar,
    Generator,
    Callable,
)
from uuid import uuid4

import pysam
import pysam.samtools
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

from scimodom.config import get_config
from scimodom.database.database import get_session
from scimodom.database.models import Dataset, BamFile, Taxa, Assembly, AssemblyVersion
from scimodom.utils.specs.enums import AssemblyFileType, TargetsFileType

logger = logging.getLogger(__name__)


DEFAULT_MODE = 0o660
COPY_BUFSIZE = 128 * 1024


def write_opener(path, flags):
    old_umask = umask(0o07)
    try:
        return os.open(path, flags, DEFAULT_MODE)
    finally:
        umask(old_umask)


class SunburstUpdateAlreadyRunning(Exception):
    """Exception for handling running chart updates."""

    pass


class FileTooLarge(Exception):
    """Exception for handling large files."""

    pass


class FileService:
    """Provide a service to interact with the file system.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param data_path: Path to DATA directory
    :type data_path: str | Path
    :param temp_path: Path to TMP directory
    :param temp_path: str | Path
    :param upload_path: Path to UPLOAD directory
    :param upload_path: str | Path
    :param import_path: Path to IMPORT directory
    :param import_path: str | Path
    """

    BUFFER_SIZE = 1024 * 1024
    VALID_FILE_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9_-]{1,256}\Z")

    ANNOTATION_DEST: ClassVar[str] = "annotation"
    GENE_CACHE_DEST: ClassVar[Path] = Path("cache", "gene", "selection")
    MOTIF_CACHE_DEST: ClassVar[Path] = Path("cache", "motifs", "PWMs_logo")
    SUNBURST_CACHE_DEST: ClassVar[Path] = Path("cache", "sunburst")
    ASSEMBLY_DEST: ClassVar[str] = "assembly"
    METADATA_DEST: ClassVar[str] = "metadata"
    REQUEST_DEST: ClassVar[str] = "project_requests"
    BAM_DEST: ClassVar[str] = "bam_files"

    def __init__(
        self,
        session: Session,
        data_path: str | Path,
        temp_path: str | Path,
        upload_path: str | Path,
        import_path: str | Path,
    ):
        self._session = session
        self._data_path = data_path
        self._temp_path = temp_path
        self._upload_path = upload_path
        self._import_path = import_path

        for path in [
            data_path,
            temp_path,
            upload_path,
            import_path,
            self._get_project_metadata_dir(),
            self._get_project_request_dir(),
            self._get_annotation_parent_dir(),
            self._get_assembly_parent_dir(),
            self._get_gene_cache_dir(),
            self._get_motif_cache_dir(),
            self._get_sunburst_cache_dir(),
            self._get_bam_files_parent_dir(),
        ]:
            self._create_folder(path)

    # General

    @staticmethod
    def open_file_for_reading(path: str | Path) -> TextIO:
        """Open a file for reading.

        :param path: File path
        :type path: str | Path
        :return: Opened file handle for reading
        :rtype: TextIO
        """
        return open(path, "r")

    @staticmethod
    def count_lines(path: str | Path) -> int:
        """Count lines in a file.

        :param path: File path
        :type path: str | Path
        :return: Number of lines.
        :rtype: bool
        """
        count = 0
        with open(path) as fp:
            while True:
                buffer = fp.read(1024 * 1024)
                if len(buffer) == 0:
                    return count
                count += buffer.count("\n")

    @staticmethod
    def _create_folder(path) -> None:
        old_umask = umask(0o07)
        try:
            makedirs(path, mode=0o2770, exist_ok=True)
        finally:
            umask(old_umask)

    @staticmethod
    @contextmanager
    def _safe_create_file(path: Path, *args, **kwargs) -> None:
        try:
            with open(path, *args, **kwargs) as fh:
                yield fh
        except Exception:
            path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _gunzip(in_path: Path, out_path: Path) -> None:
        with gzip.open(in_path, "rb") as fh_in:
            with open(out_path, "wb") as fh_out:
                copyfileobj(fh_in, fh_out, COPY_BUFSIZE)
        in_path.unlink()

    # Import

    def check_import_file(self, name: str) -> bool:
        """Check if import file exists.

        :param name: File name
        :type name: str
        :return: True if file exists, else False.
        :rtype: bool
        """
        return Path(self._import_path, name).is_file()

    def open_import_file(self, name: str) -> TextIO:
        """Import file for reading.

        :param name: File name
        :type name: str
        :return: Opened file handle for reading
        :rtype: TextIO
        """
        return open(Path(self._import_path, name))

    # Annotation incl. extended annotations (miRNA targets, RBP binding sites, etc.)

    def get_annotation_dir(self, taxa_id: int) -> Path:
        """Construct path to annotation files.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :returns: Path to annotation directory
        :rtype: Path
        """
        assembly_name = self._get_current_assembly_name_from_taxa_id(taxa_id)
        organism = self._get_organism_from_taxa_id(taxa_id)
        return Path(
            self._get_annotation_parent_dir(),
            self._get_dir_name_from_organism(organism),
            assembly_name,
        )

    def open_annotation_targets_file(
        self, taxa_id: int, target_type: TargetsFileType, chrom: str
    ) -> TextIO:
        """Open a target annotation file for reading.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param target_type: Which file to open
        :type target_type: TargetsFileType
        :param chrom: Chromosome (for split targets file)
        :type chrom: str
        :returns: File handle
        :rtype: TextIO
        """
        path = Path(self.get_annotation_dir(taxa_id), target_type.value(chrom=chrom))
        return open(path, "r")

    def _get_annotation_parent_dir(self) -> Path:
        return Path(self._data_path, self.ANNOTATION_DEST)

    # Cache

    def get_gene_cache(self, selection_id: int) -> Iterable[str]:
        """Retrieve gene list for a given selection.

        In the case that a project was created but no data was uploaded so far
        the gene cash may not be initialized and a FileNotFoundError may be
        generated.

        :param selection_id: Selection ID
        :type selection_id: int
        :returns: The genes of the selection
        :rtype: list[str]
        """
        path = Path(self._get_gene_cache_dir(), str(selection_id))
        with open(path) as fh:
            flock(fh.fileno(), LOCK_SH)
            genes = fh.read().strip().split()
            flock(fh.fileno(), LOCK_UN)
            return genes

    def update_gene_cache(self, selection_id: int, genes: Iterable[str]) -> None:
        """Update gene cache for a selection ID.

        :param selection_id: The selection_id in question.
        :type selection_id: int
        :param genes: The gene names
        :type genes: Iterable[str]
        """
        path = Path(self._get_gene_cache_dir(), str(selection_id))
        with open(path, "w", opener=write_opener) as fh:
            flock(fh.fileno(), LOCK_EX)
            for g in genes:
                print(g, file=fh)
            flock(fh.fileno(), LOCK_UN)

    def delete_gene_cache(self, selection_id: int) -> None:
        """Remove a gene cache file for a given selection.

        :param selection_id: Selection ID
        :type selection_id: int
        """
        path = Path(self._get_gene_cache_dir(), str(selection_id))
        path.unlink()

    def get_motif_logo(self, motif: str) -> Path:
        """Retrieve the logo for motif.

        :param motif: Motif ID
        :type motif: str
        """
        return Path(self._get_motif_cache_dir(), f"{motif}.PWM.png")

    def open_sunburst_cache(self, name: str) -> TextIO:
        """Open a sunburst file for reading.

        :param name: File name
        :type name: str
        :returns: Opened file handle for reading
        :rtype: TextIO
        """
        file_path = Path(self._get_sunburst_cache_dir(), f"{name}.json")
        return open(file_path)

    def update_sunburst_cache(
        self, name: str, generator: Generator[str, None, None]
    ) -> None:
        """Update a sunburst file content.

        :param name: File name
        :type name: str
        :param generator: Content to be written to file.
        :type generator: Generator
        """
        final_file_path = Path(self._get_sunburst_cache_dir(), f"{name}.json")
        try:
            temporary_file_path = None
            with NamedTemporaryFile(
                mode="w", dir=self._get_sunburst_cache_dir(), delete=False
            ) as fp:
                for data in generator:
                    fp.write(data)
                temporary_file_path = fp.name
            replace(temporary_file_path, final_file_path)
        except IOError:
            if temporary_file_path is not None and isfile(temporary_file_path):
                unlink(temporary_file_path)

    def run_sunburst_update(self, do_it: Callable[[], None]) -> None:
        """Perform a sunburst update.

        This function will run the routine passed as long as someone
        requests it. If another processes is already executing this routine,
        the duty is passed to that processes. This case is signalled
        by raising a SunburstUpdateAlreadyRunning exception.

        To communicate with other instances of itself this function uses
        a lock file 'lock' in the cache/sunburst to ensure that only one
        instance is active at any time. Another file 'update_marker' in the same
        place is used to signal that another run is required. Everyone may
        touch the marker. Only the instance holding the lock may remove it.
        By removing it, the active instance promises to do another run.

        :param do_it: Callable to perform the update
        :type do_it: Callable
        """
        lock_file = Path(self._get_sunburst_cache_dir(), "lock")
        update_marker = Path(self._get_sunburst_cache_dir(), "update_marker")
        update_marker.touch(exist_ok=True)
        with open(lock_file, "w") as fh:
            try:
                lockf(fh, LOCK_EX | LOCK_NB)
            except OSError:
                raise SunburstUpdateAlreadyRunning()
            while isfile(update_marker):
                update_marker.unlink()
                do_it()
            lockf(fh, LOCK_UN)

    def _get_gene_cache_dir(self) -> Path:
        return Path(self._data_path, self.GENE_CACHE_DEST)

    def _get_motif_cache_dir(self) -> Path:
        return Path(self._data_path, self.MOTIF_CACHE_DEST)

    def _get_sunburst_cache_dir(self) -> Path:
        return Path(self._data_path, self.SUNBURST_CACHE_DEST)

    # Project related

    def create_project_metadata_file(self, smid: str) -> TextIO:
        """Open a metadata file for writing.

        :param smid: Sci-ModoM ID (SMID)
        :type smid: str
        :returns: File handle
        :rtype: TextIO
        """
        metadata_file = Path(self._get_project_metadata_dir(), f"{smid}.json")
        return open(metadata_file, "w", opener=write_opener)

    def delete_project_metadata_file(self, smid: str) -> None:
        """Remove a metadata file.

        :param smid: Sci-ModoM ID (SMID)
        :type smid: str
        """
        path = Path(self._get_project_metadata_dir(), f"{smid}.json")
        path.unlink()

    def create_project_request_file(self, request_uuid) -> TextIO:
        """Open a metadata (request) file for writing.

        :param request_uuid: Request ID
        :type request_uuid: str
        :returns: File handle
        :rtype: TextIO
        """
        path = Path(self._get_project_request_file_path(request_uuid))
        logger.info(f"Writing project request to {path}...")
        return open(path, "w", opener=write_opener)

    def open_project_request_file(self, request_uuid) -> TextIO:
        """Open a metadata (request) file for reading.

        :param request_uuid: Request ID
        :type request_uuid: str
        :returns: File handle
        :rtype: TextIO
        """
        path = Path(self._get_project_request_file_path(request_uuid))
        return open(path, "r")

    def delete_project_request_file(self, request_uuid) -> None:
        """Remove a metadata (request) file.

        :param request_uuid: Request ID
        :type request_uuid: str
        """
        path = self._get_project_request_file_path(request_uuid)
        path.unlink()

    def _get_project_metadata_dir(self) -> Path:
        return Path(self._data_path, self.METADATA_DEST)

    def _get_project_request_file_path(self, request_uuid) -> Path:
        return Path(self._get_project_request_dir(), f"{request_uuid}.json")

    def _get_project_request_dir(self) -> Path:
        return Path(self._get_project_metadata_dir(), self.REQUEST_DEST)

    # Assembly

    def get_assembly_file_path(
        self,
        taxa_id: int,
        file_type: AssemblyFileType,
        assembly_name: str | None = None,
        chrom: str | None = None,
    ) -> Path:
        """Construct an assembly file path for a given organism.

        Provide a general constructor for all assembly file types.
        Restricted interface methods are used to interact
        with different file types (cf. below).

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file
        :type file_type: AssemblyFileType
        :param assembly_name: Assembly name. Required if file_type is CHAIN.
        If None, it is inferred from the current assembly version.
        :type assembly_name: str | None
        :param chrom: Required if file_type is DNA, DNA_IDX, or DNA_BGZ.
        :type chrom: str | None
        :raises ValueError: If missing arguments
        :return: Full path to file
        :rtype: Path
        """
        file_name = file_type.value
        current_assembly_name = self._get_current_assembly_name_from_taxa_id(taxa_id)
        if AssemblyFileType.is_chain(file_type):
            if assembly_name is None:
                raise ValueError("Missing required parameter 'assembly_name'.")
            file_name = file_type.value(
                source_assembly=assembly_name,
                target_assembly=current_assembly_name,
            )
            current_assembly_name = assembly_name
        if AssemblyFileType.is_fasta(file_type):
            if chrom is None:
                raise ValueError("Missing required parameter 'chrom'.")
            organism = self._get_dir_name_from_organism(
                self._get_organism_from_taxa_id(taxa_id)
            )
            file_name = file_type.value(
                organism=organism, assembly=current_assembly_name, chrom=chrom
            )

        return Path(self._get_assembly_dir(taxa_id, current_assembly_name), file_name)

    def open_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        """Open an assembly file for reading.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file (CHROM, INFO, RELEASE)
        :type file_type: AssemblyFileType
        :raises NotImplementedError: If file_type is CHAIN,
        DNA, DNA_IDX, DNA_BGZ.
        :return: Opened file handle for reading
        :rtype: TextIO
        """
        if AssemblyFileType.is_chain(file_type) or AssemblyFileType.is_fasta(file_type):
            raise NotImplementedError()
        path = self.get_assembly_file_path(taxa_id, file_type)
        return open(path)

    def create_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        """Open an assembly file for writing.

        If missing, the parent directory is created.
        For chain files, use create_chain_file().
        For DNA sequence files, use create_dna_sequence_file().

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file (CHROM, INFO, RELEASE)
        :type file_type: AssemblyFileType
        :raises NotImplementedError: If file_type is CHAIN,
        DNA, DNA_IDX, DNA_BGZ.
        :return: Opened file handle for writing
        :rtype: TextIO
        """
        if AssemblyFileType.is_chain(file_type) or AssemblyFileType.is_fasta(file_type):
            raise NotImplementedError()
        path = self.get_assembly_file_path(taxa_id, file_type)
        self._create_folder(path.parent)
        return open(path, "x", opener=write_opener)

    def create_chain_file(self, taxa_id: int, assembly_name: str) -> BinaryIO:
        """Create chain file for writing (binary mode).

        If missing, the parent directory is created.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param assembly_name: Assembly name
        :type assembly_name: str
        :return: Opened file handle for writing
        :rtype: BinaryIO
        """
        path = self.get_assembly_file_path(
            taxa_id,
            AssemblyFileType.CHAIN,
            assembly_name=assembly_name,
        )
        self._create_folder(path.parent)
        return open(path, "xb", opener=write_opener)

    def create_dna_sequence_file(self, taxa_id: int, chrom: str) -> BinaryIO:
        """Create DNA sequence file for writing (binary mode).

        If missing, the parent directory is created.
        If fails, the file is deleted.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param chrom: Chromosome
        :type chrom: str
        :return: Opened file handle for writing
        :rtype: BinaryIO
        """
        path = self.get_assembly_file_path(
            taxa_id,
            AssemblyFileType.DNA,
            chrom=chrom,
        )
        self._create_folder(path.parent)
        return self._safe_create_file(path, "xb", opener=write_opener)

    def index_dna_sequence_file(self, taxa_id: int, chrom: str) -> None:
        """Index a DNA sequence file.

        Use pysam (tabix for bgzip,
        samtools for faidx).

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param chrom: Chromosome
        :type chrom: str
        """
        gz_dna_sequence_file = self.get_assembly_file_path(
            taxa_id,
            AssemblyFileType.DNA,
            chrom=chrom,
        )
        dna_sequence_file = gz_dna_sequence_file.with_suffix("")
        self._gunzip(gz_dna_sequence_file, dna_sequence_file)
        pysam.tabix_compress(dna_sequence_file, gz_dna_sequence_file)
        pysam.samtools.faidx(gz_dna_sequence_file.as_posix())
        dna_sequence_file.unlink()

    def delete_assembly(self, taxa_id: int, assembly_name: str) -> None:
        """Remove assembly directory structure.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param assembly_name: Assembly name
        :type assembly_name: str
        """
        rmtree(self._get_assembly_dir(taxa_id, assembly_name))

    def check_if_assembly_exists(
        self, taxa_id: int, assembly_name: str | None = None
    ) -> bool:
        """Check if directory structure and files exist for a given assembly.

        This is done heuristically depending on the assembly.
        The file content is not validated.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param assembly_name: Assembly name. If None, it is inferred
        from the current assembly version, and this determines which
        files are checked.
        :type assembly_name: str | None
        :raises FileExistsError: If the assembly directory is in a
        corrupted state, i.e. files exist where none are expected,
        or there are missing files.
        :return: True if all required files exist, else False. An
        empty assembly directory returns False.
        :rtype: bool
        """
        current_assembly_name = self._get_current_assembly_name_from_taxa_id(taxa_id)
        # fail-safe
        if assembly_name == current_assembly_name:
            assembly_name = None

        if assembly_name is not None:
            if not self._get_assembly_dir(taxa_id, assembly_name).is_dir():
                return False
            else:
                return self.get_assembly_file_path(
                    taxa_id, AssemblyFileType.CHAIN, assembly_name=assembly_name
                ).is_file()
        else:
            assembly_dir = self._get_assembly_dir(taxa_id, current_assembly_name)
            if not assembly_dir.is_dir():
                return False
            else:
                try:
                    assembly_files = [
                        self.get_assembly_file_path(taxa_id, file_type)
                        for file_type in AssemblyFileType.common()
                    ]

                    with self.open_assembly_file(taxa_id, AssemblyFileType.CHROM) as fh:
                        chroms = [line.split()[0] for line in fh.readlines()]
                    for chrom in chroms:
                        for file_type in AssemblyFileType.fasta():
                            assembly_files.append(
                                self.get_assembly_file_path(
                                    taxa_id, file_type, chrom=chrom
                                )
                            )
                    if all(p.is_file() for p in assembly_files):
                        return True
                    else:
                        raise FileExistsError(
                            f"Files exist for assembly '{current_assembly_name}'."
                        )
                except FileNotFoundError:
                    if any(assembly_dir.iterdir()):
                        raise FileExistsError(
                            f"Files exist for assembly '{current_assembly_name}'."
                        )
                    else:
                        return False

    @staticmethod
    def _get_dir_name_from_organism(organism) -> str:
        return "_".join(organism.lower().split()).capitalize()

    def _get_assembly_parent_dir(self) -> Path:
        return Path(self._data_path, self.ASSEMBLY_DEST)

    def _get_assembly_dir(self, taxa_id: int, assembly_name: str) -> Path:
        organism = self._get_organism_from_taxa_id(taxa_id)
        return Path(
            self._get_assembly_parent_dir(),
            self._get_dir_name_from_organism(organism),
            assembly_name,
        )

    def _get_organism_from_taxa_id(self, taxa_id: int) -> str:
        return self._session.execute(
            select(Taxa.name).filter_by(id=taxa_id)
        ).scalar_one()

    def _get_current_assembly_name_from_taxa_id(self, taxa_id: int) -> str:
        return self._session.execute(
            select(Assembly.name)
            .join(AssemblyVersion, Assembly.version == AssemblyVersion.version_num)
            .where(Assembly.taxa_id == taxa_id)
        ).scalar_one()

    # uploaded files

    def upload_tmp_file(self, stream, max_file_size) -> str:
        fp, path = mkstemp(dir=self._upload_path)
        close(fp)
        file_id = basename(path)
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise Exception(
                f"Internal Error: Tmp file basename ({file_id}) is not valid!"
            )
        self._stream_to_file(stream, path, max_file_size, overwrite_is_ok=True)
        return file_id

    def open_tmp_upload_file_by_id(self, file_id: str) -> TextIO:
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise ValueError("open_tmp_file_by_id called with bad file_id")
        path = join(self._upload_path, file_id)
        return open(path)

    def check_tmp_upload_file_id(self, file_id: str) -> bool:
        path = join(self._upload_path, file_id)
        return isfile(path)

    def _stream_to_file(
        self, data_stream, path, max_size, overwrite_is_ok=False
    ) -> None:
        if exists(path) and not overwrite_is_ok:
            raise Exception(
                f"FileService._stream_to_file(): Refusing to overwrite existing file: '{path}'!"
            )
        self._create_folder(dirname(path))
        try:
            bytes_written = 0
            with open(path, "wb", opener=write_opener) as fp:
                while True:
                    buffer = data_stream.read(self.BUFFER_SIZE)
                    if len(buffer) == 0:
                        break
                    fp.write(buffer)
                    bytes_written += len(buffer)
                    if max_size is not None and bytes_written > max_size:
                        raise FileTooLarge(
                            f"The file is too large (max {max_size} bytes)"
                        )
        except Exception as exc:
            self._handle_upload_error(exc, path)

    # intermediate files

    def create_temp_file(self, suffix="") -> str:
        fp, path = mkstemp(dir=self._temp_path, suffix=suffix)
        close(fp)
        return path

    @staticmethod
    def read_sequence_context(fasta_file: str) -> str:
        try:
            with open(fasta_file, "r") as fh:
                sequence = fh.readlines()[1].strip()
        except IndexError:
            sequence = ""
        return sequence

    # BAM file

    def create_or_update_bam_file(
        self,
        dataset: Dataset,
        name: str,
        data_stream: IO[bytes],
        max_size: Optional[int],
    ) -> None:
        try:
            bam_file = self.get_bam_file(dataset, name)
            self._update_bam_file(bam_file, data_stream, max_size)
        except NoResultFound:
            self._create_bam_file(dataset, name, data_stream, max_size)

    def get_bam_file(self, dataset: Dataset, name: str) -> BamFile:
        return self._session.scalars(
            select(BamFile).where(
                and_(
                    BamFile.dataset_id == dataset.id, BamFile.original_file_name == name
                )
            )
        ).one()

    def open_bam_file(self, bam_file: BamFile) -> IO[bytes]:
        path = self._get_bam_file_path(bam_file)
        return open(path, "rb")

    def get_bam_file_list(self, dataset: Dataset) -> List[Dict[str, Any]]:
        items = self._session.scalars(
            select(BamFile).where(BamFile.dataset_id == dataset.id)
        ).all()
        return [self._get_bam_file_info(i) for i in items]

    def remove_bam_file(self, bam_file: BamFile) -> None:
        path = self._get_bam_file_path(bam_file)
        try:
            unlink(path)
        except FileNotFoundError:
            pass
        self._session.delete(bam_file)
        self._session.commit()

    @staticmethod
    def _handle_upload_error(exception, path) -> None:
        logger.warning(
            f"Failed to create file '{path}': {str(exception)} - discarding file."
        )
        try:
            unlink(path)
        except Exception as unlink_e:
            logger.warning(f"Failed to delete '{path}': {str(unlink_e)}.")
        raise exception

    def _get_bam_files_parent_dir(self) -> Path:
        return Path(self._data_path, self.BAM_DEST)

    def _update_bam_file(self, bam_file, data_stream, max_size) -> None:
        tmp_path = self._get_bam_file_tmp_path(bam_file)
        path = self._get_bam_file_path(bam_file)
        self._stream_to_file(data_stream, tmp_path, max_size)
        try:
            unlink(path)
        except FileNotFoundError:
            pass
        try:
            rename(tmp_path, path)
        except Exception as exc:
            logger.error(
                f"Failed to move '{tmp_path}' to '{path}': {str(exc)} - discarding database entry!"
            )
            self._session.delete(bam_file)
            raise exc

    def _get_bam_file_tmp_path(self, bam_file) -> str:
        return join(
            self._get_bam_files_parent_dir().as_posix(),
            f"tmp.{bam_file.storage_file_name}",
        )

    def _get_bam_file_path(self, bam_file) -> str:
        return join(
            self._get_bam_files_parent_dir().as_posix(), bam_file.storage_file_name
        )

    def _create_bam_file(self, dataset, name, data_stream, max_size) -> None:
        bam_file = BamFile(
            dataset_id=dataset.id,
            original_file_name=name,
            storage_file_name=f"{dataset.id}_{uuid4()}_{name}"[:256],
        )
        path = self._get_bam_file_path(bam_file)
        self._stream_to_file(data_stream, path, max_size)
        self._session.add(bam_file)
        self._session.commit()

    def _get_bam_file_info(self, bam_file) -> dict[str, Any]:
        path = self._get_bam_file_path(bam_file)
        stat_info = stat(path)
        return {
            "original_file_name": bam_file.original_file_name,
            "size_in_bytes": stat_info.st_size,
            "mtime_epoch": stat_info.st_mtime,
        }


@cache
def get_file_service() -> FileService:
    """Instantiate a FileService object by injecting its dependencies.

    :returns: File service instance
    :rtype: FileService
    """
    config = get_config()
    return FileService(
        get_session(),
        data_path=config.DATA_PATH,
        temp_path=config.BEDTOOLS_TMP_PATH,
        upload_path=config.UPLOAD_PATH,
        import_path=config.IMPORT_PATH,
    )
