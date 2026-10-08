import pytest

from scimodom.api.dataset import dataset_api
from scimodom.services.dataset import DatasetService
from scimodom.services.exporter import Exporter
from scimodom.services.permission import PermissionService
from scimodom.services.url import DATASET_API_ROUTE
from scimodom.services.user import UserService
from scimodom.utils.dtos.dataset import DatasetPostRequest
from tests.api.schematise import validate, client_fixture

SCHEMA = "dataset.yaml"

client = client_fixture(dataset_api, DATASET_API_ROUTE)
auth_client = client_fixture(dataset_api, DATASET_API_ROUTE, authenticated=True)

DATASET_REQUEST = DatasetPostRequest(
    project_id="12345678",
    file_id="test.bed",
    rna_type="WTS",
    modification_id=[1],
    organism_id=1,
    assembly_id=1,
    technology_id=1,
    title="Test",
)


@pytest.fixture
def services(Session, dataset, mocker):
    mock_validator = mocker.Mock()
    mock_validator.get_validated_records.return_value = []
    dataset_service = DatasetService(
        session=Session(),
        annotation_service=mocker.Mock(),
        file_service=mocker.Mock(),
        validator_service=mock_validator,
    )
    mocker.patch(
        "scimodom.api.dataset.get_dataset_service",
        return_value=dataset_service,
    )
    mock_file_service = mocker.MagicMock()
    mock_file_service.open_tmp_upload_file_by_id.return_value.__enter__.return_value = (
        "content"
    )
    mocker.patch(
        "scimodom.api.dataset.get_file_service",
        return_value=mock_file_service,
    )
    user_service = UserService(
        session=Session(),
        mail_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.dataset.get_user_service",
        return_value=user_service,
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_user_service",
        return_value=user_service,
    )
    permission_service = PermissionService(Session())
    mocker.patch(
        "scimodom.api.dataset.get_permission_service",
        return_value=permission_service,
    )
    exporter = Exporter(Session())
    mocker.patch(
        "scimodom.api.dataset.get_exporter",
        return_value=exporter,
    )
    mocker.patch(
        "scimodom.api.dataset.get_sunburst_service",
        return_value=mocker.Mock(),
    )


def prefix_url(path: str) -> str:
    return f"{DATASET_API_ROUTE}{path}"


def test_datasets_schema(client, services):
    response = client.get(prefix_url("/datasets"))
    assert response.json
    validate(SCHEMA, response, 200)


def test_datasets_summary_schema(client, services):
    response = client.get(prefix_url("/datasets/summary"))
    validate(SCHEMA, response, 200)


def test_my_datasets_schema(auth_client, services):  # noqa: F811
    response = auth_client.get(prefix_url("/users/me/datasets"))
    assert response.json
    validate(SCHEMA, response, 200)


def test_permissions_schema(auth_client, services):
    response = auth_client.get(
        prefix_url("/users/me/datasets/dataset00001/permissions")
    )
    validate(SCHEMA, response, 200)


def test_export_schema(client, services):
    response = client.get(prefix_url("/datasets/dataset00001/bedrmod"))
    validate(SCHEMA, response, 200)


def test_add_dataset_schema(auth_client, services):
    response = auth_client.post(
        prefix_url("/datasets"), json=DATASET_REQUEST.model_dump()
    )
    validate(SCHEMA, response, 201)
