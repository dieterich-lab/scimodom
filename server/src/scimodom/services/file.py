import logging
from os import unlink, rename, makedirs
from os.path import join, exists, dirname
from typing import Optional, IO
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import and_

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.database.models import Dataset, BamFile


logger = logging.getLogger(__name__)


class FileService:
    BUFFER_SIZE = 1024 * 1024

    def __init__(self, session: Session):
        self._db_session = session

    def create_or_update_bam_file(
        self, dataset: Dataset, name: str, data_stream: IO[bytes]
    ):
        try:
            bam_file = self.get_bam_file(dataset, name)
            self._update_bam_file(bam_file, data_stream)
        except NoResultFound:
            self._create_bam_file(dataset, name, data_stream)

    def get_bam_file(self, dataset: Dataset, name: str) -> BamFile:
        return self._db_session.scalars(
            select(BamFile).where(
                and_(
                    BamFile.dataset_id == dataset.id, BamFile.original_file_name == name
                )
            )
        ).one()

    def _update_bam_file(self, bam_file, data_stream):
        tmp_path = self._get_bam_file_tmp_path(bam_file)
        path = self._get_bam_file_path(bam_file)
        self._stream_to_file(data_stream, tmp_path)
        try:
            unlink(path)
        except FileNotFoundError:
            pass
        try:
            rename(tmp_path, path)
        except Exception as e:
            logger.error(
                f"ERROR: Failed to move '{tmp_path} to {path}: {str(e)} - discarding database entry!'"
            )
            self._db_session.delete(bam_file)
            raise e

    @staticmethod
    def _get_bam_file_tmp_path(bam_file):
        return join(
            join(Config.DATA_PATH, "bam_files"), f"tmp.{bam_file.storage_file_name}"
        )

    @staticmethod
    def _get_bam_file_path(bam_file):
        return join(join(Config.DATA_PATH, "bam_files"), bam_file.storage_file_name)

    def _stream_to_file(self, data_stream, path):
        if exists(path):
            raise Exception(
                f"FileService._stream_to_file(): Refusing to overwrite existing file: '{path}'!"
            )
        parent = dirname(path)
        if not exists(parent):
            makedirs(path)
        try:
            with open(path, "wb") as fp:
                while True:
                    buffer = data_stream.read(self.BUFFER_SIZE)
                    if len(buffer) == 0:
                        break
                    fp.write(buffer)
        except Exception as e:
            logger.warning(
                f"Failed to create file '{path}': {str(e)} - discarding file."
            )
            try:
                unlink(path)
            except Exception as unlink_e:
                logger.warning(f"Failed to to delete '{path}': {str(unlink_e)}.")
            raise e

    def _create_bam_file(self, dataset, name, data_stream):
        bam_file = BamFile(
            dataset_id=dataset.id,
            original_file_name=name,
            storage_file_name=f"{dataset.id}_{uuid4()}_name"[:256],
        )
        path = self._get_bam_file_path(bam_file)
        self._stream_to_file(data_stream, path)
        self._db_session.add(bam_file)
        self._db_session.commit()


_cached_file_service: Optional[FileService] = None


def get_file_service() -> FileService:
    global _cached_file_service
    if _cached_file_service is None:
        _cached_file_service = FileService(get_session())
    return _cached_file_service