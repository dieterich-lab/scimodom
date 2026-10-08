import pytest

from scimodom.api.comparison import dataset_comparison_api
from scimodom.services.url import DATASET_COMPARISON_API_ROUTE

# NOTE: all mocks
from tests.api.test_comparison_api import (  # noqa: F401
    MockFileService,
    MockValidatorService,
    get_compare_url_parameters,
    mock_services,
)
from tests.api.schematise import validate, client_fixture

SCHEMA = "comparison.yaml"
client = client_fixture(dataset_comparison_api, DATASET_COMPARISON_API_ROUTE)

OPERATIONS = ["intersect", "closest", "subtract"]

UPLOAD = MockFileService.VALID_TEMP_FILE_ID


def prefix_url(operation, *args, **kwargs):
    return f"{DATASET_COMPARISON_API_ROUTE}{get_compare_url_parameters(operation, *args, **kwargs)}"


@pytest.mark.parametrize("operation", OPERATIONS)
class TestComparisonSchema:
    def test_two_datasets(self, client, mock_services, operation):  # noqa: F811
        response = client.get(prefix_url(operation, ["datasetidAxx"], ["datasetidBxx"]))
        validate(SCHEMA, response, 200)

    def test_dataset_lists(self, client, mock_services, operation):  # noqa: F811
        response = client.get(
            prefix_url(
                operation,
                ["datasetidAxx", "datasetidBxx"],
                ["datasetidCxx"],
                strand=False,
            )
        )
        validate(SCHEMA, response, 200)

    def test_uploaded_euf_file(self, client, mock_services, operation):  # noqa: F811
        response = client.get(
            prefix_url(
                operation, ["datasetidBxx"], upload=UPLOAD, euf=True, taxa_id=9606
            )
        )
        validate(SCHEMA, response, 200)

    def test_uploaded_bed6_file(self, client, mock_services, operation):  # noqa: F811
        response = client.get(prefix_url(operation, ["datasetidAxx"], upload=UPLOAD))
        validate(SCHEMA, response, 200)
