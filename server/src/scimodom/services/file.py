import logging
import re
from enum import Enum
from fcntl import flock, LOCK_SH, LOCK_EX, LOCK_UN
from functools import cache
from os import unlink, rename, makedirs, stat, close
from os.path import join, exists, dirname, basename, isfile
from pathlib import Path
from shutil import rmtree
from tempfile import mkstemp
from typing import Optional, IO, List, Dict, TextIO, BinaryIO, Iterable, Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

from scimodom.config import get_config
from scimodom.database.database import get_session
from scimodom.database.models import Dataset, BamFile, Taxa, Assembly, AssemblyVersion

logger = logging.getLogger(__name__)


class FileTooLarge(Exception):
    pass


class AssemblyFileType(Enum):
    CHROM = "chrom.sizes"
    INFO = "info.json"
    RELEASE = "release.json"
    CHAIN = "__CHAIN__"


class FileService:
    BUFFER_SIZE = 1024 * 1024
    VALID_FILE_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9_-]{1,256}\Z")

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
            temp_path,
            upload_path,
            self._get_gene_cache_dir(),
            self.get_annotation_dir(),
            self.get_project_metadata_dir(),
        ]:
            makedirs(path, exist_ok=True)

    # generic

    @staticmethod
    def count_lines(path: str | Path):
        count = 0
        with open(path) as fp:
            while True:
                buffer = fp.read(1024 * 1024)
                if len(buffer) == 0:
                    return count
                count += buffer.count("\n")

    # import

    def check_import_file(self, name: str):
        return Path(self._import_path, name).is_file()

    def open_import_file(self, name: str):
        return open(Path(self._import_path, name))

    # annotation

    def get_annotation_dir(self) -> Path:
        """Construct parent path to annotation files.

        :returns: Path to annotation
        :rtype: Path
        """
        return Path(self._data_path, "annotation")

    # Gene Cache

    def get_gene_cache(self, selection_ids: Iterable[int]) -> list[str]:
        """Retrieve gene list for a given selection.

        :param selection_ids: Selection ID(s)
        :type selection_ids: Iterable[int]
        :returns: The genes of the selection
        :rtype: list[str]
        """
        result = set()
        for selection_id in selection_ids:
            path = Path(self._get_gene_cache_dir(), str(selection_id))
            with open(path) as fh:
                flock(fh.fileno(), LOCK_SH)
                genes = set(fh.read().strip().split())
                flock(fh.fileno(), LOCK_UN)
            result = result | genes
        return list(result)

    def update_gene_cache(self, selection_id: int, genes: Iterable[str]) -> None:
        """Update gene cache for a selection ID.

        :param selection_id: The selection_id in question.
        :type selection_id: int
        :param genes: The gene names
        :type genes: Iterable[str]
        """
        path = Path(self._get_gene_cache_dir(), str(selection_id))
        with open(path, "w") as fh:
            flock(fh.fileno(), LOCK_EX)
            for g in genes:
                print(g, file=fh)
            flock(fh.fileno(), LOCK_UN)

    def _get_gene_cache_dir(self) -> Path:
        return Path(self._data_path, "cache", "gene", "selection")

    # Project related

    def get_project_metadata_dir(self) -> Path:
        """Construct parent path to metadata.

        :returns: Path to metadata
        :rtype: Path
        """
        return Path(self._data_path, "metadata")

    def create_project_metadata_file(self, smid: str) -> TextIO:
        """Open a metadata file for writing.

        :param smid: Sci-ModoM ID (SMID)
        :type smid: str
        :returns: File handle
        :rtype: TextIO
        """
        metadata_file = Path(self.get_project_metadata_dir(), f"{smid}.json")
        return open(metadata_file, "w")

    def create_project_request_file(self, request_uuid) -> TextIO:
        """Open a metadata (request) file for writing.

        :param smid: Request ID
        :type smid: str
        :returns: File handle
        :rtype: TextIO
        """
        path = Path(self._get_project_request_file_path(request_uuid))
        logger.info(f"Writing project request to {path}...")
        return open(path, "w")

    def open_project_request_file(self, request_uuid) -> TextIO:
        """Open a metadata (request) file for reading.

        :param smid: Request ID
        :type smid: str
        :returns: File handle
        :rtype: TextIO
        """
        path = Path(self._get_project_request_file_path(request_uuid))
        return open(path, "r")

    def delete_project_request_file(self, request_uuid) -> None:
        """Remove a metadata (request) file.

        :param smid: Request ID
        :type smid: str
        """
        path = self._get_project_request_file_path(request_uuid)
        path.unlink()

    def _get_project_request_file_path(self, request_uuid):
        return Path(self._get_project_request_dir(), f"{request_uuid}.json")

    def _get_project_request_dir(self):
        return Path(self.get_project_metadata_dir(), "project_requests")

    # Assembly

    def get_assembly_file_path(
        self,
        taxa_id: int,
        file_type: AssemblyFileType,
        chain_file_name: str | None = None,
        chain_assembly_name: str | None = None,
    ) -> Path:
        """Construct assembly-related file paths for a given organism.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file (CHROM, INFO, RELEASE, CHAIN)
        :type file_type: AssemblyFileType
        :param chain_file_name: Only used if file_type is CHAIN - base chain file name
        :type chain_file_name: str
        :param assembly_name: Only used if file_type is CHAIN - assembly name
        :type assembly_name: str
        :returns: Full path to file
        :rtype: Path
        """
        file_name = file_type.value
        assembly_name = self._get_current_assembly_name_from_taxa_id(taxa_id)
        if file_type == AssemblyFileType.CHAIN:
            if chain_file_name is None or chain_assembly_name is None:
                raise ValueError("Missing chain_file_name and/or assembly_name!")
            file_name = chain_file_name
            assembly_name = chain_assembly_name

        return Path(self._get_assembly_dir(taxa_id, assembly_name), file_name)

    def open_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        """Opens an assembly file path for a given organism and returns a file for reading.
        Chain files are not supported.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file (CHROM, INFO, RELEASE, CHAIN)
        :type file_type: AssemblyFileType
        """
        if file_type == AssemblyFileType.CHAIN:
            raise NotImplementedError()
        path = self.get_assembly_file_path(taxa_id, file_type)
        return open(path)

    def create_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        """Open an assembly file for writing for a given organism.
        If missing, the parent directory is created.
        Chain files are not supported. Use create_chain_file() instead.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_type: Type of assembly file (CHROM, INFO, RELEASE, CHAIN)
        :type file_type: AssemblyFileType
        """
        if file_type == AssemblyFileType.CHAIN:
            raise NotImplementedError()
        path = self.get_assembly_file_path(taxa_id, file_type)
        makedirs(path.parent, exist_ok=True)
        return open(path, "x")

    def create_chain_file(
        self, taxa_id: int, file_name: str, assembly_name
    ) -> BinaryIO:
        """Creates chain file for a given organism and returns a file handle to fill it.
        If missing, the parent directory is created.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param file_name: Chain file name
        :type file_name: str
        :param assembly_name: Assembly name
        :type assembly_name: str
        :returns: Writable file handle
        :rtype: BinaryIO
        """
        path = self.get_assembly_file_path(
            taxa_id,
            AssemblyFileType.CHAIN,
            chain_file_name=file_name,
            chain_assembly_name=assembly_name,
        )
        makedirs(path.parent, exist_ok=True)
        return open(path, "xb")

    def delete_assembly(self, taxa_id: int, assembly_name: str) -> None:
        """Remove assembly directory structure

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param name: Assembly name
        :type name: str
        """
        rmtree(self._get_assembly_dir(taxa_id, assembly_name))

    def check_if_assembly_exists(self, taxa_id: int, name: str) -> bool:
        """Check if directory structure exists for a given assembly.

        :param taxa_id: Taxa ID
        :type taxa_id: int
        :param name: Assembly name
        :type name: str
        """
        return self._get_assembly_dir(taxa_id, name).is_dir()

    @staticmethod
    def _get_dir_name_from_organism(organism) -> str:
        return "_".join(organism.lower().split()).capitalize()

    def _get_assembly_dir(self, taxa_id: int, assembly_name: str) -> Path:
        organism = self._get_organism_from_taxa_id(taxa_id)
        return Path(
            self._data_path,
            "assembly",
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

    def upload_tmp_file(self, stream, max_file_size):
        fp, path = mkstemp(dir=self._upload_path)
        close(fp)
        file_id = basename(path)
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise Exception(
                f"Internal Error: Tmp file basename ({file_id}) is not valid!"
            )
        self._stream_to_file(stream, path, max_file_size, overwrite_is_ok=True)
        return file_id

    def _stream_to_file(self, data_stream, path, max_size, overwrite_is_ok=False):
        if exists(path) and not overwrite_is_ok:
            raise Exception(
                f"FileService._stream_to_file(): Refusing to overwrite existing file: '{path}'!"
            )
        parent = dirname(path)
        if not exists(parent):
            makedirs(path)
        try:
            bytes_written = 0
            with open(path, "wb") as fp:
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

    def open_tmp_upload_file_by_id(self, file_id: str) -> TextIO:
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise ValueError("open_tmp_file_by_id called with bad file_id")
        path = join(self._upload_path, file_id)
        return open(path)

    def check_tmp_upload_file_id(self, file_id: str) -> bool:
        path = join(self._upload_path, file_id)
        return isfile(path)

    # intermediate files

    def create_temp_file(self, suffix="") -> str:
        fp, path = mkstemp(dir=self._temp_path, suffix=suffix)
        close(fp)
        return path

    def get_temp_path(self) -> str:
        return self._temp_path

    # BAM file

    def create_or_update_bam_file(
        self,
        dataset: Dataset,
        name: str,
        data_stream: IO[bytes],
        max_size: Optional[int],
    ):
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

    def _update_bam_file(self, bam_file, data_stream, max_size):
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

    def _get_bam_file_tmp_path(self, bam_file):
        return join(
            join(self._data_path, "bam_files"), f"tmp.{bam_file.storage_file_name}"
        )

    def _get_bam_file_path(self, bam_file):
        return join(join(self._data_path, "bam_files"), bam_file.storage_file_name)

    @staticmethod
    def _handle_upload_error(exception, path):
        logger.warning(
            f"Failed to create file '{path}': {str(exception)} - discarding file."
        )
        try:
            unlink(path)
        except Exception as unlink_e:
            logger.warning(f"Failed to delete '{path}': {str(unlink_e)}.")
        raise exception

    def _create_bam_file(self, dataset, name, data_stream, max_size):
        bam_file = BamFile(
            dataset_id=dataset.id,
            original_file_name=name,
            storage_file_name=f"{dataset.id}_{uuid4()}_{name}"[:256],
        )
        path = self._get_bam_file_path(bam_file)
        self._stream_to_file(data_stream, path, max_size)
        self._session.add(bam_file)
        self._session.commit()

    def open_bam_file(self, bam_file: BamFile) -> IO[bytes]:
        path = self._get_bam_file_path(bam_file)
        return open(path, "rb")

    def get_bam_file_list(self, dataset: Dataset) -> List[Dict[str, Any]]:
        items = self._session.scalars(
            select(BamFile).where(BamFile.dataset_id == dataset.id)
        ).all()
        return [self._get_bam_file_info(i) for i in items]

    def _get_bam_file_info(self, bam_file):
        path = self._get_bam_file_path(bam_file)
        stat_info = stat(path)
        return {
            "original_file_name": bam_file.original_file_name,
            "size_in_bytes": stat_info.st_size,
            "mtime_epoch": stat_info.st_mtime,
        }

    def remove_bam_file(self, bam_file: BamFile):
        path = self._get_bam_file_path(bam_file)
        try:
            unlink(path)
        except FileNotFoundError:
            pass
        self._session.delete(bam_file)
        self._session.commit()


@cache
def get_file_service() -> FileService:
    config = get_config()
    return FileService(
        get_session(),
        data_path=config.DATA_PATH,
        temp_path=config.BEDTOOLS_TMP_PATH,
        upload_path=config.UPLOAD_PATH,
        import_path=config.IMPORT_PATH,
    )
