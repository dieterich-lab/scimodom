import logging
import shlex
import sys
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, Popen, run
from threading import Thread

from scimodom.services.file import FileService, get_file_service
from scimodom.utils.specs.enums import IndexCacheType

logger = logging.getLogger(__name__)


class ExternalService:
    """Utility class to communicate with external services or programs.

    :param file_service: A file service instance
    """

    def __init__(self, file_service: FileService):
        self._file_service = file_service

    @staticmethod
    def trigger_cache_update(cache: IndexCacheType | None = None) -> None:
        """Update the caches of the index in the background.

        Concurrent updates are coalesced by the lock in the
        file service, see `_run_detached` for details.

        :param cache: The cache to update, or all caches if None
        """
        cmd = "update" if cache is None else f"update-{cache.value}"
        ExternalService._run_detached(
            [sys.executable, "-m", "flask", "--app", "scimodom.app", "cache", cmd]
        )

    def get_crossmap_output(
        self,
        raw_file: str,
        chain_file: str,
        unmapped: str | None = None,
        chrom_id: str = "s",
    ) -> tuple[str, str]:
        """Liftover features from raw_file using CrossMap.

        A file is returned pointing to the liftedOver features.
        The unmapped features are saved as "unmapped", or discarded.

        :param raw_file: File to liftover
        :param chain_file: Chain file
        :param unmapped: File to write unmapped features
        :param chrom_id: The style of chromosome IDs (default s).
        :return: Files with liftedOver and unmapped features
        """
        result = self._file_service.create_temp_file(suffix=".bed")
        if unmapped is None:
            unmapped = self._file_service.create_temp_file(suffix=".bed")
        cmd = f"CrossMap bed --chromid {chrom_id} --unmap-file {unmapped} {chain_file} {raw_file} {result}"
        self._run(cmd, "CrossMap")
        return result, unmapped

    @staticmethod
    def _run(
        cmd: str,
        caller: str,
        check: bool = True,
        capture_output: bool = True,
        text: bool = True,
    ):
        """Run cmd in a blocking subprocess."""
        logger.debug(f"Calling: {cmd}")
        try:
            run(
                shlex.split(cmd),
                check=check,
                capture_output=capture_output,
                text=text,
            )
        except FileNotFoundError as exc:
            raise Exception(f"Process failed: {caller} could not be found!") from exc
        except CalledProcessError as exc:
            raise Exception(f"Process failed with {exc.stderr}")
        # except subprocess.TimeoutExpired as exc:

    @staticmethod
    def _run_detached(cmd: Sequence[str]) -> None:
        """Run cmd in a subprocess and return immediately.

        Run in a new session with the interpreter of the
        current process, fully detached from the caller,
        cannot hang waiting for input, and is reaped to avoid
        zombie processes in a long-running server.
        """
        logger.debug(f"Calling (detached): {cmd}")
        process = Popen(list(cmd), stdin=DEVNULL, start_new_session=True)
        Thread(target=process.wait, daemon=True).start()

    @staticmethod
    def call_cmalign(
        model_file: str, fasta_file: str, sto: str, out: str, outfmt: str = "Stockholm"
    ) -> None:
        """Align multiple sequences to a common covariance model
        using Infernal (cmalign), mostly for tRNA annotation.

        :param mode_file: Covariance model file
        :type mode_file: str
        :param fasta_file: File with FASTA sequences
        :type fasta_file: str
        :param sto: File name to write alignments
        :type sto: str
        :param out: File name to write alignment scores
        :type fasta_file: str
        :param outfmt: Alignment format
        :type outfmt: str
        """
        cmd = f"cmalign --outformat {outfmt} -o {sto} --sfile {out} {model_file} {fasta_file}"
        ExternalService._run(cmd, "cmalign")

    @staticmethod
    def call_ss_consensus(sto: str, sprinzl: str, tab: str) -> None:
        """Add Sprinzl coordinates to consensus.

        :param sto: Alignments
        :type sto: str
        :param sprinzl_file: File with Sprinzl coordinates
        :type sprinzl: str
        :param tab: Output file name
        :type tab: str
        """
        cmd = f"ss_consensus_add_sprinzl {sto} --sprinzl {sprinzl} --output {tab}"
        ExternalService._run(cmd, "ss_consensus_add_sprinzl")

    @staticmethod
    def call_to_sprinzl(tab: str, sto: str, out: str) -> None:
        """Create sequence to Sprinzl mapping.

        :param sto: Alignments
        :type sto: str
        :param tab: Intermediate file with consensus and Sprinzl
        :type tab: str
        :param out: Output file with mapping
        :type out: str
        """
        cmd = f"seq_to_sprinzl {tab} {sto} --output {out}"
        ExternalService._run(cmd, "seq_to_sprinzl")

    @staticmethod
    def get_sprinzl_mapping(model_file: str, fasta_file: str, sprinzl_file: str) -> str:
        """Create a "mapping" between sequence and
        Sprinzl or cloverleaf positions.

        NOTE: The executables are packaged from
        https://github.com/dieterich-lab/QutRNA/
        (downsampling branch 14.06.2024). Input files
        are not validated for consistency (taxonomic
        domain, organism, and/or Sprinzl coordinates).

        :param mode_file: Covariance model file
        :type mode_file: str
        :param fasta_file: File with FASTA sequences
        :type fasta_file: str
        :param sprinzl_file: File with Sprinzl coordinates
        :type sprinzl_file: str
        :returns: Output file with mapping. The path is
        constructed using "fasta_file".
        :rtype: str
        """
        fasta_path = Path(fasta_file)
        stem = fasta_path.stem
        parent = fasta_path.parent
        sto = Path(parent, stem).with_suffix(".sto").as_posix()
        out = Path(parent, stem).with_suffix(".out").as_posix()
        tab = Path(parent, stem).with_suffix(".tab").as_posix()
        mapping = Path(parent, "seq_to_sprinzl.tab").as_posix()

        ExternalService.call_cmalign(model_file, fasta_file, sto, out)
        ExternalService.call_ss_consensus(sto, sprinzl_file, tab)
        ExternalService.call_to_sprinzl(tab, sto, mapping)
        return mapping


@cache
def get_external_service():
    """Instantiate an ExternalService object by injecting its dependencies.

    :return: External service instance
    """
    return ExternalService(file_service=get_file_service())
