import pytest
from flask import Flask

from sqlalchemy.exc import NoResultFound

from scimodom.api.catalog import catalog_api


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(catalog_api, url_prefix="")
    yield app.test_client()


@pytest.mark.parametrize(
    "selection,http_status,message",
    [
        ("?selection=1&selection=2", 404, "No data for selection(s) '1, 2'"),
        ("", 400, "Missing required parameter: 'selection'"),
    ],
)
def test_get_genes(test_client, mocker, selection, http_status, message):
    mock_gene_service = mocker.Mock()
    mock_gene_service.get_genes.side_effect = NoResultFound
    mocker.patch(
        "scimodom.api.catalog.get_gene_service",
        return_value=mock_gene_service,
    )
    result = test_client.get(f"genes{selection}")
    assert result.status_code == http_status
    assert result.json["message"] == message


def test_get_features(test_client, mocker):
    mock_annotation_service = mocker.Mock()
    mock_annotation_service.get_features_by_rna_type.side_effect = NotImplementedError
    mocker.patch(
        "scimodom.api.catalog.get_annotation_service",
        return_value=mock_annotation_service,
    )
    mocker.patch("scimodom.api.catalog.parse_valid_rna_type", return_value="type")
    url = "rna-types/type/features"
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
        "scimodom.api.catalog.get_assembly_service",
        return_value=mock_assembly_service,
    )
    mocker.patch("scimodom.api.catalog.get_valid_taxa_id", return_value=9606)
    result = test_client.get("chromosomes?taxaId=9606")
    assert result.status_code == 404
    assert result.json["message"] == f"No chrom data for taxaId '9606' ({index})"


def test_get_chroms_requires_taxa(test_client, mocker):
    # chromosomes exist for the current assembly of a taxon only, so
    # there is no unfiltered collection to return
    mock_assembly_service = mocker.Mock()
    mocker.patch(
        "scimodom.api.catalog.get_assembly_service",
        return_value=mock_assembly_service,
    )
    result = test_client.get("chromosomes")
    assert result.status_code == 400
    assert result.json["message"] == "Missing required parameter: 'taxaId'"
    mock_assembly_service.get_chroms.assert_not_called()


CATALOG_ROUTES = [("assemblies", "assembly"), ("annotations", "annotation")]


@pytest.mark.parametrize("route,service", CATALOG_ROUTES)
def test_get_catalog_no_filter(test_client, mocker, route, service):
    # taxaId is optional: without it every organism is reported
    mock_service = mocker.Mock()
    getattr(mock_service, f"get_{route}").return_value = []
    mocker.patch(
        f"scimodom.api.catalog.get_{service}_service", return_value=mock_service
    )
    result = test_client.get(route)
    assert result.status_code == 200
    assert result.json == []


@pytest.mark.parametrize("route,service", CATALOG_ROUTES)
def test_get_catalog_by_taxa(test_client, mocker, route, service):
    mock_service = mocker.Mock()
    getattr(mock_service, f"get_{route}").return_value = []
    mocker.patch(
        f"scimodom.api.catalog.get_{service}_service", return_value=mock_service
    )
    mocker.patch("scimodom.api.helpers.validation._validate_taxa_id", return_value=None)
    result = test_client.get(f"{route}?taxaId=9606")
    assert result.status_code == 200


@pytest.mark.parametrize("route,service", CATALOG_ROUTES)
@pytest.mark.parametrize(
    "taxa_id,http_status,message",
    [
        ("abc", 400, "Parameter 'taxaId' must be a valid _positive_int (got: 'abc')"),
        ("-1", 400, "Parameter 'taxaId' must be a positive integer"),
        ("1", 404, "taxaId '1' not found"),
    ],
)
def test_get_catalog_invalid_taxa(
    test_client, mocker, route, service, taxa_id, http_status, message
):
    mock_service = mocker.Mock()
    getattr(mock_service, f"get_{route}").return_value = []
    mocker.patch(
        f"scimodom.api.catalog.get_{service}_service", return_value=mock_service
    )
    mock_utilities_service = mocker.Mock()
    mock_utilities_service.get_taxa.return_value = []
    mocker.patch(
        "scimodom.api.helpers.validation.get_utilities_service",
        return_value=mock_utilities_service,
    )
    result = test_client.get(f"{route}?taxaId={taxa_id}")
    assert result.status_code == http_status
    assert result.json["message"] == message
    getattr(mock_service, f"get_{route}").assert_not_called()


@pytest.mark.parametrize(
    "query,expected",
    [("", None), ("?current=true", True), ("?current=false", False)],
)
def test_get_assemblies_current(test_client, mocker, query, expected):
    # absent means unfiltered, as before the flat endpoint existed
    mock_assembly_service = mocker.Mock()
    mock_assembly_service.get_assemblies.return_value = []
    mocker.patch(
        "scimodom.api.catalog.get_assembly_service",
        return_value=mock_assembly_service,
    )
    result = test_client.get(f"assemblies{query}")
    assert result.status_code == 200
    mock_assembly_service.get_assemblies.assert_called_once_with(None, expected)


def test_get_assemblies_invalid_current(test_client, mocker):
    # an unrecognised value is rejected, not silently ignored
    mock_assembly_service = mocker.Mock()
    mocker.patch(
        "scimodom.api.catalog.get_assembly_service",
        return_value=mock_assembly_service,
    )
    result = test_client.get("assemblies?current=1")
    assert result.status_code == 400
    mock_assembly_service.get_assemblies.assert_not_called()
