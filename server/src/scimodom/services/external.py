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

    @staticmethod
    def run(
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
        ExternalService.run(cmd, "cmalign")

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
        ExternalService.run(cmd, "ss_consensus_add_sprinzl")

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
        ExternalService.run(cmd, "seq_to_sprinzl")

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

    def get_crossmap_output(
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
        self.run(cmd, "CrossMap")
        return result, unmapped


@cache
def get_external_service():
    return ExternalService(file_service=get_file_service())
