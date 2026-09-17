import pytest
from flask import Flask

from sqlalchemy.exc import NoResultFound

from scimodom.api.utilities import api


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(api, url_prefix="")
    yield app.test_client()


def test_get_genes(test_client, mocker):
    mock_gene_service = mocker.Mock()
    mock_gene_service.get_genes.side_effect = NoResultFound
    mocker.patch(
        "scimodom.api.utilities.get_gene_service",
        return_value=mock_gene_service,
    )
    url = "genes?selection=1&selection=2"
    result = test_client.get(url)
    assert result.status_code == 404
    assert result.json["message"] == "No data for selection(s) '1, 2'"


def test_get_features(test_client, mocker):
    mock_annotation_service = mocker.Mock()
    mock_annotation_service.get_features_by_rna_type.side_effect = NotImplementedError
    mocker.patch(
        "scimodom.api.utilities.get_annotation_service",
        return_value=mock_annotation_service,
    )
    mocker.patch("scimodom.api.utilities.parse_valid_rna_type", return_value="type")
    url = "features/type"
    result = test_client.get(url)
    assert result.status_code == 501
    assert result.json["message"] == "rnaType 'type' not implemented"


@pytest.mark.parametrize(
    "error,index",
    [
        (NoResultFound, 1),
        (FileNotFoundError, 2),
    ],
)
def test_get_chroms(test_client, mocker, error, index):
    mock_assembly_service = mocker.Mock()
    mock_assembly_service.get_chroms.side_effect = error
    mocker.patch(
        "scimodom.api.utilities.get_assembly_service",
        return_value=mock_assembly_service,
    )
    mocker.patch("scimodom.api.utilities.parse_valid_taxa_id", return_value=9606)
    url = "chroms/9606"
    result = test_client.get(url)
    assert result.status_code == 404
    assert result.json["message"] == f"No chrom data for taxaId '9606' ({index})"


def test_get_assemblies(test_client, mocker):
    mock_assembly_service = mocker.Mock()
    mock_assembly_service.get_assemblies_by_taxa.return_value = []
    mocker.patch(
        "scimodom.api.utilities.get_assembly_service",
        return_value=mock_assembly_service,
    )
    mocker.patch("scimodom.api.utilities.parse_valid_taxa_id", return_value=9606)
    url = "assemblies/9606"
    result = test_client.get(url)
    assert result.status_code == 200
    assert result.json == []
