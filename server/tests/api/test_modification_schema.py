import pytest

from scimodom.api.modification import modification_api
from scimodom.services.annotation import (
    AnnotationService,
    EnsemblAnnotationService,
)
from scimodom.services.data import DataService
from scimodom.services.gene import GeneService
from scimodom.services.modification import ModificationService, MultiSortError
from scimodom.services.url import MODIFICATION_API_ROUTE
from scimodom.services.utilities import UtilitiesService
from scimodom.utils.specs.enums import AnnotationSource, AssemblyFileType

# the mocks of the existing API tests are reused: same services, same data
# from tests.api.test_modification_api import (  # noqa: F401
#     MockModificationService,
#     mock_services,
# )
from tests.unit.services.test_modification import _mock_build_query
from tests.api.test_modification_api import (
    MockAssemblyService,
    MockFileService,
    MockBedtoolsService,
)
from tests.api.schematise import validate, client_fixture

SCHEMA = "modification.yaml"

client = client_fixture(modification_api, MODIFICATION_API_ROUTE)

BY_SELECTION = "modification=1&organism=1&technology=2&rnaType=WTS&taxaId=9606"
BY_GENE = "by=gene&rnaType=WTS&taxaId=9606&geneName=GENE1"
SITE = "chrom=1&chromStart=20652450&chromEnd=20652451&strand=-&taxaId=9606"
TARGET_SITE = "taxaId=9606&chrom=1&chromStart=3284723&chromEnd=3284724&strand=%2B"


@pytest.fixture
def services(Session, annotation, mocker):
    utilities_service = UtilitiesService(Session())
    mocker.patch(
        "scimodom.api.helpers.validation.get_utilities_service",
        return_value=utilities_service,
    )
    data_service = DataService(session=Session())
    gene_service = GeneService(session=Session(), file_service=MockFileService())
    annotation_service = AnnotationService(
        session=Session(),
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=Session(),
                data_service=data_service,
                bedtools_service=MockBedtoolsService(),
                external_service=mocker.Mock(),
                web_service=mocker.Mock(),
                gene_service=gene_service,
                file_service=MockFileService(),
            ),
        },
    )
    modification_service = ModificationService(
        session=Session(),
        annotation_service=annotation_service,
    )
    mocker.patch.object(modification_service, "_build_query", _mock_build_query)
    mocker.patch(
        "scimodom.api.helpers.validation.get_annotation_service",
        return_value=annotation_service,
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_assembly_service",
        return_value=MockAssemblyService(),
    )
    mocker.patch(
        "scimodom.api.modification.get_modification_service",
        return_value=modification_service,
    )
    mocker.patch(
        "scimodom.api.modification.get_bedtools_service",
        return_value=MockBedtoolsService(),
    )
    mocker.patch(
        "scimodom.api.modification.get_file_service",
        return_value=MockFileService(),
    )


def prefix_url(path: str) -> str:
    return f"{MODIFICATION_API_ROUTE}{path}"


@pytest.mark.parametrize("query", [BY_SELECTION, BY_GENE])
def test_records_schema(client, services, query):
    response = client.get(prefix_url(f"/records?{query}"))
    assert response.json["records"]
    validate(SCHEMA, response, 200)


@pytest.mark.parametrize("query", [BY_SELECTION, BY_GENE])
def test_records_csv_schema(client, services, query):
    response = client.get(prefix_url(f"/records?format=csv&{query}"))
    validate(SCHEMA, response, 200)


def test_records_summary_schema(client, services):
    response = client.get(prefix_url("/records/summary"))
    validate(SCHEMA, response, 200)


def test_sites_schema(client, services):
    response = client.get(prefix_url(f"/sites?{SITE}"))
    assert response.json["records"]
    validate(SCHEMA, response, 200)


def test_sites_summary_schema(client, services):
    response = client.get(prefix_url("/sites/summary"))
    validate(SCHEMA, response, 200)


def test_context_schema(client, services):
    response = client.get(prefix_url(f"/sites/context?window=1&{SITE}"))
    validate(SCHEMA, response, 200)


@pytest.mark.parametrize("target", ["MIRNA", "RBP"])
def test_targets_schema(client, services, target):
    response = client.get(prefix_url(f"/sites/targets?target={target}&{TARGET_SITE}"))
    assert response.json["records"]
    validate(SCHEMA, response, 200)
