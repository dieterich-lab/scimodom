import logging
from functools import cache
import shlex
from subprocess import run, CalledProcessError

from scimodom.services.file import FileService, get_file_service


logger = logging.getLogger(__name__)


class CrossMapService:
    def __init__(self, file_service: FileService):
        self._file_service = file_service

    def liftover_file(
        self,
        raw_file: str,
        chain_file: str,
        unmapped: str | None = None,
        chrom_id: str = "s",
    ) -> tuple[str, str]:
        """Liftover records. Handles conversion to BedTool, but not from,
        of the liftedOver features. A file is returned pointing
        to the liftedOver features. The unmapped ones are saved as
        "unmapped", or discarded.

        :param raw_file: File name of o BED file to liftover
        :type raw_file: str
        :param chain_file: Chain file
        :type chain_file: str
        :param unmapped: File to write unmapped features
        :type unmapped: str or None
        :param chrom_id: The style of chromosome IDs (default s).
        :type chrom_id: str
        :returns: Files with liftedOver and unmapped features
        :rtype: tuple of (str, str)
        """
        result = self._file_service.create_temp_file(suffix=".bed")
        if unmapped is None:
            unmapped = self._file_service.create_temp_file(suffix=".bed")
        cmd = f"CrossMap bed --chromid {chrom_id} --unmap-file {unmapped} {chain_file} {raw_file} {result}"
        logger.debug(f"Calling: {cmd}")

        # set a timeout?
        try:
            run(shlex.split(cmd), check=True, capture_output=True, text=True)
        except FileNotFoundError as exc:
            msg = "Process failed: CrossMap executable could not be found!"
            raise Exception(msg) from exc
        except CalledProcessError as exc:
            msg = f"Process failed with {exc.stderr}"
            raise Exception(msg) from exc
        # except subprocess.TimeoutExpired as exc:
        return result, unmapped


@cache
def get_cross_map_service():
    return CrossMapService(file_service=get_file_service())
