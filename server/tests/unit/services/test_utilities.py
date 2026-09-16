import pytest

from scimodom.services.utilities import UtilitiesService


@pytest.fixture
def utilities_service(Session):
    yield UtilitiesService(
        session=Session(),
    )


def test_get_rna_types(Session, utilities_service, setup):
    expected_rna_types = [{"id": "WTS", "label": "whole transcriptome"}]
    assert utilities_service.get_rna_types() == expected_rna_types


def test_get_taxa(Session, utilities_service, setup):
    expected_taxa = [
        {
            "taxa_id": 7227,
            "taxa_name": "Drosophila melanogaster",
            "taxa_sname": "D. melanogaster",
            "domain": "Eukarya",
            "kingdom": "Animalia",
            "phylum": "Arthropoda",
        },
        {
            "taxa_id": 9606,
            "taxa_name": "Homo sapiens",
            "taxa_sname": "H. sapiens",
            "domain": "Eukarya",
            "kingdom": "Animalia",
            "phylum": "Chordata",
        },
        {
            "taxa_id": 10090,
            "taxa_name": "Mus musculus",
            "taxa_sname": "M. musculus",
            "domain": "Eukarya",
            "kingdom": "Animalia",
            "phylum": "Chordata",
        },
    ]
    assert utilities_service.get_taxa() == expected_taxa


def test_get_biotypes(Session, utilities_service, mocker):
    mocker.patch(
        "scimodom.services.utilities.MAPPED_BIOTYPES",
        ["biotype 1", "biotype 2"],
    )

    assert utilities_service.get_biotypes() == {"biotypes": ["biotype 1", "biotype 2"]}


def test_get_modomics(Session, utilities_service, setup):
    expected_modomics = [
        {"id": "2000000006A", "modomics_sname": "m6A"},
        {"id": "2000000005C", "modomics_sname": "m5C"},
        {"id": "2000000009U", "modomics_sname": "Y"},
    ]
    assert utilities_service.get_modomics() == expected_modomics


def test_get_methods(Session, utilities_service, setup):
    expected_methods = [
        {
            "id": "0ee048bc",
            "cls": "NGS 2nd generation",
            "meth": "Chemical-assisted sequencing",
        },
        {
            "id": "91b145ea",
            "cls": "NGS 2nd generation",
            "meth": "Antibody-based sequencing",
        },
        {
            "id": "01d26feb",
            "cls": "NGS 2nd generation",
            "meth": "Enzyme/protein-assisted sequencing",
        },
    ]
    assert utilities_service.get_methods() == expected_methods


def test_get_selection(Session, utilities_service, selection):
    expected_selection = {
        "modification_id": 1,
        "rna": "WTS",
        "rna_name": "whole transcriptome",
        "modomics_sname": "m6A",
        "technology_id": 1,
        "cls": "NGS 2nd generation",
        "meth": "Antibody-based sequencing",
        "tech": "Technology 1",
        "organism_id": 1,
        "domain": "Eukarya",
        "kingdom": "Animalia",
        "taxa_id": 9606,
        "taxa_name": "Homo sapiens",
        "taxa_sname": "H. sapiens",
        "cto": "Cell type 1",
        "selection_id": 1,
    }
    selections = utilities_service.get_selections()
    assert len(selections) == 5
    assert selections[0] == expected_selection


def test_get_release_info(Session, utilities_service, dataset):
    expected_info = {"sites": 7, "datasets": 4}
    assert utilities_service.get_release_info() == expected_info
