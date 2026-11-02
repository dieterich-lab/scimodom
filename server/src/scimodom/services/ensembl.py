"""Remote access to Ensembl for assembly data.

NOTE: Everything is derived from :class:`scimodom.utils.specs.enums.Ensembl`.
"""

import re
from functools import cache
from posixpath import join as urljoin
from typing import Any

from scimodom.services.web import WebService, get_web_service
from scimodom.utils.specs.enums import AssemblyFileType, Ensembl


class EnsemblAssemblyClient:
    """Build Ensembl URLs and query the Ensembl REST API for assembly data.

    This class has no knowledge of the database or of the local file
    system layout. It does not download files, URLs are returned to the
    caller (AssembyService) for orchestration.

    :param web_service: The web service
    """

    # ENS[3-letter species code]<feature type: G|T|P|E...><11 digits>[.version]
    _STABLE_ID = re.compile(r"^(ENS(?:[A-Z]{3})?)[A-Z]\d{11}(?:\.\d+)?$")

    TOP_LEVEL_COORD_SYSTEMS = ["chromosome", "primary_assembly"]
    INFO_KEYS = [
        "assembly_accession",
        "assembly_date",
        "assembly_name",
        "coord_system_versions",
    ]

    def __init__(self, web_service: WebService) -> None:
        self._web_service = web_service

    @staticmethod
    def get_organism_url_name(organism: str) -> str:
        """Convert an organism name to the name used in Ensembl URLs.

        :param organism: Organism name e.g. "Homo sapiens"
        :return: Name for use in URLs e.g. "homo_sapiens"
        """
        return "_".join(organism.split()).lower()

    @classmethod
    def get_ensembl_prefix(cls, gene_id: str) -> str:
        """Extract the prefix incl. species code of an Ensembl stable identifier.

        :param gene_id: Ensembl stable identifier, optionally with version
        :raises ValueError: If not an Ensembl stable ID.
        :return: The prefix
        """
        match = cls._STABLE_ID.match(gene_id)
        if match is None:
            raise ValueError(f"Not an Ensembl stable identifier: '{gene_id}'")
        return match.group(1)

    # REST

    @staticmethod
    def get_coord_system_version(gene_build: dict[str, Any]) -> str:
        """Get default coordinate system version.

        :param gene_build: Gene build, cf. get_gene_build
        :return: Assembly name
        """
        return gene_build["default_coord_system_version"]

    @classmethod
    def get_top_level_regions(
        cls, gene_build: dict[str, Any]
    ) -> tuple[list[str], dict[str, int]]:
        """Get the karyotype and the length of the top level.

        :param gene_build: Gene build, cf. get_gene_build
        :return: Chromosome names (karyotype), and lengths by name
        """
        chroms = gene_build["karyotype"]
        top_level = {
            d["name"]: d["length"]
            for d in gene_build["top_level_region"]
            if d["coord_system"] in cls.TOP_LEVEL_COORD_SYSTEMS and d["name"] in chroms
        }
        return chroms, top_level

    @classmethod
    def get_assembly_info(cls, gene_build: dict[str, Any]) -> dict[str, Any]:
        """Get the assembly info to be saved from a gene build.

        :param gene_build: Gene build, cf. get_gene_build
        :return: Assembly info
        """
        return {k: v for k, v in gene_build.items() if k in cls.INFO_KEYS}

    def get_data_release(self) -> dict:
        """Query the REST API for the data release(s).

        :return: Response as json
        """
        url = urljoin(Ensembl.REST.value, Ensembl.DATA.value)
        return self._web_service.request_as_json(url)

    def get_gene_build(self, organism: str) -> dict:
        """Query the REST API for the gene build (assembly info) of an organism.

        :param organism: Organism name e.g. "Homo sapiens"
        :return: Response as json
        """
        url = urljoin(
            Ensembl.REST.value,
            Ensembl.ASM.value,
            self.get_organism_url_name(organism),
        )
        return self._web_service.request_as_json(url)

    # FTP

    def get_chain_file_url(
        self, organism: str, source_assembly: str, target_assembly: str
    ) -> str:
        """Construct the URL of a chain file.

        :param organism: Organism name e.g. "Homo sapiens"
        :param source_assembly: Source assembly name
        :param target_assembly: Target assembly name
        :return: URL
        """
        chain_file_name = AssemblyFileType.CHAIN.value(
            source_assembly=source_assembly,
            target_assembly=target_assembly,
        )
        return urljoin(
            Ensembl.FTP.value,
            Ensembl.ASM_MAPPING.value,
            self.get_organism_url_name(organism),
            chain_file_name,
        )

    def get_dna_sequence_urls(
        self, organism: str, assembly_name: str, chrom: str
    ) -> list[str]:
        """Construct the candidate URLs of a chromosome DNA sequence file.

        "chromosome" or "primary_assembly": candidates are returned in
        the order in which they should be tried, i.e. "chromosome" first.

        :param organism: Organism name e.g. "Homo sapiens"
        :param assembly_name: Assembly name
        :param chrom: Chromosome
        :return: Candidate URLs
        """
        url_name = self.get_organism_url_name(organism)
        seq_file_name = AssemblyFileType.DNA.value(
            organism=url_name.capitalize(), assembly=assembly_name, chrom=chrom
        )
        seq_file_names = [seq_file_name, AssemblyFileType.get_alt_name(seq_file_name)]
        return [
            urljoin(
                Ensembl.FTP.value,
                Ensembl.FASTA.value,
                url_name,
                "dna",
                name,
            )
            for name in seq_file_names
        ]


@cache
def get_ensembl_assembly_client() -> EnsemblAssemblyClient:
    """Instantiate an EnsemblAssemblyClient object by injecting its dependencies.

    :return: Ensembl assembly client instance
    """
    return EnsemblAssemblyClient(
        web_service=get_web_service(),
    )
