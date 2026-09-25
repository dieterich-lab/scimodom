from smtplib import SMTPException

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from scimodom.api.management import management_api
from scimodom.services.assembly import LiftOverError
from scimodom.services.validator import (
    SelectionNotFoundError,
    DatasetImportError,
    DatasetHeaderError,
    DatasetExistsError,
    SpecsError,
)
from scimodom.utils.importer.bed_importer import (
    BedImportTooManyErrors,
    BedImportEmptyFile,
)


@pytest.fixture
def authenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(management_api, url_prefix="")
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="test-user")
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    yield client


@pytest.fixture
def unauthenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(management_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def project_mocks(mocker):
    mock_project_service = mocker.Mock()
    mock_project_service.create_project_request.return_value = 123
    mocker.patch(
        "scimodom.api.management.get_project_service",
        return_value=mock_project_service,
    )
    mock_mail_service = mocker.Mock()
    mock_mail_service.send_project_request_notification.return_value = None
    mocker.patch(
        "scimodom.api.management.get_mail_service",
        return_value=mock_mail_service,
    )


@pytest.fixture
def dataset_mocks(mocker):
    mock_dataset_service = mocker.Mock()
    mock_dataset_service.import_dataset.return_value = None
    mocker.patch(
        "scimodom.api.management.get_dataset_service",
        return_value=mock_dataset_service,
    )
    mock_file_service = mocker.Mock()
    mock_file_service.check_tmp_upload_file_id.return_value = True
    mock_file_service.open_tmp_upload_file_by_id = mocker.mock_open()
    mocker.patch(
        "scimodom.api.management.get_file_service",
        return_value=mock_file_service,
    )
    mock_dataset_post_request = mocker.Mock()
    mock_dataset_post_request.file_id = "test.bed"
    mocker.patch(
        "scimodom.api.management.DatasetPostRequest.model_validate_json",
        return_value=mock_dataset_post_request,
    )
    mocker.patch(
        "scimodom.api.management.parse_valid_rna_type",
        return_value="any",
    )
    mocker.patch(
        "scimodom.api.management.AnnotationService.get_annotation_source",
        return_value=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.management.validate_project_write_permission",
        return_value=None,
    )
    mock_sunburst_service = mocker.Mock()
    mock_sunburst_service.trigger_background_update.return_value = None
    mocker.patch(
        "scimodom.api.management.get_sunburst_service",
        return_value=mock_sunburst_service,
    )
    yield mock_file_service


def test_create_project_request(authenticated_client, mocker, project_mocks):
    mock_project_template = mocker.Mock()
    mocker.patch(
        "scimodom.api.management.ProjectTemplate.model_validate_json",
        return_value=mock_project_template,
    )
    result = authenticated_client.post("project", json={"field": "value"})
    assert result.status_code == 200
    assert result.json["message"] == "OK"


def test_create_project_request_invalid_model(authenticated_client, project_mocks):
    result = authenticated_client.post("project", json={})
    assert result.status_code == 400
    assert (
        result.json["message"]
        == "Request body validation: malformed and/or bad/missing fields"
    )


def test_create_project_request_invalid_json(authenticated_client, project_mocks):
    result = authenticated_client.post(
        "project", data='{"title"}', content_type="application/json"
    )
    assert result.status_code == 400
    assert (
        result.json["message"]
        == "Request body validation: malformed and/or bad/missing fields"
    )


def test_create_project_request_smtp_exception(authenticated_client, mocker, caplog):
    mock_project_service = mocker.Mock()
    mock_project_service.create_project_request.return_value = 123
    mocker.patch(
        "scimodom.api.management.get_project_service",
        return_value=mock_project_service,
    )
    mock_mail_service = mocker.Mock()
    mock_mail_service.send_project_request_notification.side_effect = SMTPException(
        "oups"
    )
    mocker.patch(
        "scimodom.api.management.get_mail_service",
        return_value=mock_mail_service,
    )
    mocker.patch(
        "scimodom.api.management.ProjectTemplate.model_validate_json",
        return_value=mocker.Mock(),
    )
    result = authenticated_client.post("project", json={})
    assert result.status_code == 500
    assert (
        result.json["message"]
        == "Request '123' created, but an unexpected error occurred during submission. Contact the system administrator."
    )
    assert caplog.messages[0] == "Notification failed for project '123': oups"


def test_create_project_request_unauthenticated(unauthenticated_client, mocker):
    mock_project_service = mocker.patch("scimodom.api.management.get_project_service")
    result = unauthenticated_client.post("project", json={"field": "value"})
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"
    mock_project_service.assert_not_called()
