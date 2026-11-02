import pytest

from scimodom.services.ensembl import EnsemblAssemblyClient
from tests.mocks.enums import MockEnsembl
from tests.mocks.web import MockWebService

GENE_BUILD = {
    "default_coord_system_version": "GRCh38",
    "assembly_name": "GRCh38.p14",
    "assembly_date": "2013-12",
    "assembly_accession": "GCA_000001405.29",
    "coord_system_versions": ["GRCh38"],
    "karyotype": ["1", "2"],
    "top_level_region": [
        {"name": "1", "length": 10, "coord_system": "chromosome"},
        {"name": "2", "length": 20, "coord_system": "primary_assembly"},
        {"name": "3", "length": 30, "coord_system": "chromosome"},
        {"name": "1", "length": 99, "coord_system": "scaffold"},
    ],
    "other": "dropped",
}


@pytest.fixture
def client(mocker):
    mocker.patch("scimodom.services.ensembl.Ensembl", MockEnsembl)
    return EnsemblAssemblyClient(
        MockWebService(
            url_to_result={
                "http://jul2023.rest.ensembl.org/info/data": {"releases": [110]},
                "http://jul2023.rest.ensembl.org/info/assembly/homo_sapiens": GENE_BUILD,
            }
        )
    )


@pytest.mark.parametrize(
    "gene_id, expected",
    [
        ("ENSG00000139618", "ENS"),
        ("ENSG00000139618.5", "ENS"),
        ("ENST00000380152", "ENS"),
        ("ENSMUSG00000017167", "ENSMUS"),
        ("ENSDARG00000000001", "ENSDAR"),
    ],
)
def test_get_ensembl_prefix(gene_id, expected):
    assert EnsemblAssemblyClient.get_ensembl_prefix(gene_id) == expected


@pytest.mark.parametrize("gene_id", ["", "foo", "ENSG1", "ENSG00000139618x"])
def test_get_ensembl_prefix_fail(gene_id):
    with pytest.raises(ValueError, match="Not an Ensembl stable identifier"):
        EnsemblAssemblyClient.get_ensembl_prefix(gene_id)


def test_organism_url_name():
    assert (
        EnsemblAssemblyClient.get_organism_url_name("Homo  Sapiens") == "homo_sapiens"
    )


def test_rest(client):
    assert client.get_data_release() == {"releases": [110]}
    assert client.get_gene_build("Homo sapiens") == GENE_BUILD


def test_gene_build_parsing():
    assert EnsemblAssemblyClient.get_coord_system_version(GENE_BUILD) == "GRCh38"
    chroms, top = EnsemblAssemblyClient.get_top_level_regions(GENE_BUILD)
    assert chroms == ["1", "2"]
    assert top == {"1": 10, "2": 20}
    info = EnsemblAssemblyClient.get_assembly_info(GENE_BUILD)
    assert set(info) == set(EnsemblAssemblyClient.INFO_KEYS)


def test_chain_file_url(client):
    assert client.get_chain_file_url("Homo sapiens", "GRCh37", "GRCh38") == (
        "https://ftp.ensembl.org/pub/release-110/assembly_chain/homo_sapiens/"
        "GRCh37_to_GRCh38.chain.gz"
    )


def test_dna_sequence_urls(client):
    urls = client.get_dna_sequence_urls("Homo sapiens", "GRCh38", "1")
    assert len(urls) == 2
    assert "dna.chromosome.1" in urls[0]
    assert "dna.primary_assembly.1" in urls[1]
    assert urls[0].startswith(
        "https://ftp.ensembl.org/pub/release-110/fasta/homo_sapiens/dna/"
    )
