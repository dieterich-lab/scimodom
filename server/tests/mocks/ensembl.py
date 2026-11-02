from typing import Any

from scimodom.services.ensembl import EnsemblAssemblyClient
from tests.mocks.web import MockHTTPError

GENE_BUILD = {
    "assembly_accession": "GCA_000001405.29",
    "assembly_date": "2013-12",
    "assembly_name": "GRCh38.p14",
    "coord_system_versions": ["GRCh38", "GRCh37", "NCBI36", "NCBI35", "NCBI34"],
    "default_coord_system_version": "GRCh38",
    "karyotype": ["1", "2", "X"],
    "top_level_region": [
        {"coord_system": "chromosome", "length": 248956422, "name": "1"},
        {"coord_system": "chromosome", "length": 242193529, "name": "2"},
        {"coord_system": "chromosome", "length": 156040895, "name": "X"},
    ],
}

NEWEST_GENE_BUILD = {**GENE_BUILD, "default_coord_system_version": "GRCh39"}


class MockEnsemblClient:
    """Stand-in for EnsemblAssemblyClient with canned responses.

    The pure parsing helpers are those of the real client (they are
    tested with it). Everything that would need the network, or that
    depends on the Ensembl URL layout, is faked. If no gene build
    (release) is given, the request fails like an unknown URL would.
    """

    get_organism_url_name = staticmethod(EnsemblAssemblyClient.get_organism_url_name)
    get_coord_system_version = staticmethod(
        EnsemblAssemblyClient.get_coord_system_version
    )
    get_top_level_regions = staticmethod(EnsemblAssemblyClient.get_top_level_regions)
    get_assembly_info = staticmethod(EnsemblAssemblyClient.get_assembly_info)

    def __init__(
        self,
        gene_build: dict[str, Any] | None = None,
        release: dict[str, Any] | None = None,
    ) -> None:
        self._gene_build = gene_build
        self._release = release

    def get_data_release(self) -> dict:
        if self._release is None:
            raise MockHTTPError("Mock: Not found!")
        return self._release

    def get_gene_build(self, organism: str) -> dict:
        if self._gene_build is None:
            raise MockHTTPError("Mock: Not found!")
        return self._gene_build

    @staticmethod
    def get_chain_file_url(organism: str, source_assembly: str, target_assembly: str):
        return f"mock://chain/{source_assembly}_to_{target_assembly}"

    @staticmethod
    def get_dna_sequence_urls(organism: str, assembly_name: str, chrom: str):
        return [
            f"mock://dna/chromosome.{chrom}",
            f"mock://dna/primary_assembly.{chrom}",
        ]
