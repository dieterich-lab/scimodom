import logging
from functools import cache
from pathlib import Path
import shlex
from subprocess import run, CalledProcessError

from scimodom.services.file import FileService, get_file_service


logger = logging.getLogger(__name__)


class ExternalService:
    def __init__(self, file_service: FileService):
        self._file_service = file_service

    def _run(
        self,
        cmd: str,
        caller: str,
        check: bool = True,
        capture_output: bool = True,
        text: bool = True,
    ):
        """Run cmd in a blocking subprocess.

        :param cmd: Command to execute
        :type cmd: str
        :param caller: Name of executable
        :type caller: str
        """
        logger.debug(f"Calling: {cmd}")
        # set a timeout?
        try:
            run(shlex.split(cmd), check=check, capture_output=capture_output, text=text)
        except FileNotFoundError as exc:
            raise Exception(f"Process failed: {caller} could not be found!") from exc
        except CalledProcessError as exc:
            raise Exception(f"Process failed with {exc.stderr}")
        # except subprocess.TimeoutExpired as exc:

    def call_crossmap(
        self,
        raw_file: str,
        chain_file: str,
        unmapped: str | None = None,
        chrom_id: str = "s",
    ) -> tuple[str, str]:
        """Liftover features from raw_file using CrossMap. A file is
        returned pointing to the liftedOver features. The unmapped
        ones are saved as "unmapped", or discarded.

        :param raw_file: File to liftover
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
        self._run(cmd, "CrossMap")
        return result, unmapped

    def call_cmalign(
        self, model_file: str, fasta_file: str, outfmt: str = "Stockholm"
    ) -> str:
        """Align multiple sequences to a common covariance model
        using Infernal (cmalign), mostly for tRNA annotation.

        :param mode_file: Covariance model file
        :type mode_file: str | Path
        :param fasta_file: File with FASTA sequences
        :type fasta_file: str | Path
        :param destination: Output directory
        :type destination: Path
        :param outfmt: Alignment format
        :type outfmt: str
        :returns: Output file with alignments. The path is
        constructed using "fasta_file".
        :rtype: str
        """
        fasta_path = Path(fasta_file)
        stem = fasta_path.stem
        parent = fasta_path.parent
        sto = Path(parent, stem).with_suffix(".sto").as_posix()
        out = Path(parent, stem).with_suffix(".out").as_posix()
        cmd = f"cmalign --outformat {outfmt} -o {sto} --sfile {out} {model_file} {fasta_file}"
        self._run(cmd, "cmalign")
        return sto


@cache
def get_external_service():
    return ExternalService(file_service=get_file_service())
