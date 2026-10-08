import os
from contextlib import contextmanager
from io import BytesIO

import pytest

from scimodom.api.attachment import dataset_attachment_api
from scimodom.services.file import FileService
from scimodom.services.dataset import DatasetService
from scimodom.services.permission import PermissionService
from scimodom.services.url import DATASET_ATTACHMENT_API_ROUTE
from scimodom.services.user import UserService
from tests.api.schematise import validate, client_fixture

SCHEMA = "attachment.yaml"
client = client_fixture(dataset_attachment_api, DATASET_ATTACHMENT_API_ROUTE)
auth_client = client_fixture(
    dataset_attachment_api, DATASET_ATTACHMENT_API_ROUTE, authenticated=True
)


@pytest.fixture
def services(Session, bam_file, mocker, tmp_path):
    @contextmanager
    def open_bam_file(_):
        yield BytesIO(b"BAM\x01 some bytes")

    mock_stat = os.stat_result(
        (0o100644, 1, 2, 1, 0, 0, 1234, 0, 1_700_000_000, 1_700_000_000)
    )

    file_service = FileService(
        Session(),
        data_path=(tmp_path / "DATA_PATH"),
        temp_path=(tmp_path / "BEDTOOLS_TMP_PATH"),
        upload_path=(tmp_path / "UPLOAD_PATH"),
        import_path=(tmp_path / "IMPORT_PATH"),
    )
    file_service.open_bam_file = open_bam_file
    mocker.patch.object(
        file_service, "create_or_update_bam_file", return_value="created"
    )
    mocker.patch.object(file_service, "remove_bam_file", return_value=mocker.Mock())
    mocker.patch("scimodom.services.file.stat", return_value=mock_stat)

    dataset_service = DatasetService(
        session=Session(),
        annotation_service=mocker.Mock(),
        file_service=file_service,
        validator_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_dataset_service",
        return_value=dataset_service,
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_file_service",
        return_value=file_service,
    )
    mocker.patch(
        "scimodom.api.attachment.get_file_service",
        return_value=file_service,
    )
    permission_service = PermissionService(Session())
    mocker.patch(
        "scimodom.api.helpers.validation.get_permission_service",
        return_value=permission_service,
    )
    user_service = UserService(
        session=Session(),
        mail_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.helpers.validation.get_user_service",
        return_value=user_service,
    )
    return file_service


def prefix_url(path: str) -> str:
    return f"{DATASET_ATTACHMENT_API_ROUTE}/dataset00001/attachments/bams{path}"


def test_bams_schema(client, services):
    response = client.get(prefix_url(""))
    assert response.json
    validate(SCHEMA, response, 200)


def test_get_bam_schema(client, services):
    response = client.get(prefix_url("/dataset00001_1.bam"))
    validate(SCHEMA, response, 200)


def test_put_bam_create_schema(auth_client, services):
    response = auth_client.put(prefix_url("/put.bam"), data=b"bytes")
    validate(SCHEMA, response, 201)


def test_put_bam_update_schema(auth_client, services):
    services.create_or_update_bam_file.return_value = "updated"
    response = auth_client.put(prefix_url("/dataset00001_1.bam"), data=b"bytes")
    validate(SCHEMA, response, 204)


def test_delete_bam(auth_client, services):
    response = auth_client.delete(prefix_url("/dataset00001_1.bam"))
    validate(SCHEMA, response, 204)
