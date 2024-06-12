import logging
import re
from functools import cache
from os import unlink, rename, makedirs, stat, close
from os.path import join, exists, dirname, basename, isfile
from tempfile import mkstemp
from typing import Optional, IO, List, Dict
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.database.models import Dataset, BamFile

logger = logging.getLogger(__name__)


class FileTooLarge(Exception):
    pass


class FileService:
    BUFFER_SIZE = 1024 * 1024
    VALID_FILE_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9_-]{1,256}\Z")

    def __init__(self, session: Session):
        self._db_session = session

    # general

    def upload_tmp_file(self, stream, max_file_size):
        fp, path = mkstemp(dir=Config.UPLOAD_PATH)
        close(fp)
        file_id = basename(path)
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise Exception(
                f"Internal Error: Tmp file basename ({file_id}) is not valid!"
            )
        self._stream_to_file(stream, path, max_file_size, overwrite_is_ok=True)
        return file_id

    def open_tmp_file_by_id(self, file_id):
        if not self.VALID_FILE_ID_REGEXP.match(file_id):
            raise ValueError("open_tmp_file_by_id called with bad file_id")
        path = join(Config.UPLOAD_PATH, file_id)
        return open(path)

    @staticmethod
    def check_tmp_file_id(file_id: str) -> bool:
        path = join(Config.UPLOAD_PATH, file_id)
        return isfile(path)

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
        return self._db_session.scalars(
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
            self._db_session.delete(bam_file)
            raise exc

    @staticmethod
    def _get_bam_file_tmp_path(bam_file):
        return join(
            join(Config.DATA_PATH, "bam_files"), f"tmp.{bam_file.storage_file_name}"
        )

    @staticmethod
    def _get_bam_file_path(bam_file):
        return join(join(Config.DATA_PATH, "bam_files"), bam_file.storage_file_name)

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
        self._db_session.add(bam_file)
        self._db_session.commit()

    def open_bam_file(self, bam_file: BamFile) -> IO[bytes]:
        path = self._get_bam_file_path(bam_file)
        return open(path, "rb")

    def get_bam_file_list(self, dataset: Dataset) -> List[Dict[str, any]]:
        items = self._db_session.scalars(
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
        self._db_session.delete(bam_file)
        self._db_session.commit()


@cache
def get_file_service() -> FileService:
    return FileService(get_session())
