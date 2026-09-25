import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from scimodom.api.attachment import dataset_attachment_api
from scimodom.services.file import FileTooLarge


@pytest.fixture
def unauthenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(dataset_attachment_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def authenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(dataset_attachment_api, url_prefix="")
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="test-user")
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    yield client


# tests


def test_put_bam_unauthenticated(unauthenticated_client, mocker):
    mock_validate = mocker.patch("scimodom.api.attachment.get_valid_dataset")
    response = unauthenticated_client.put(
        "/d1/attachments/bams/name",
        data=b"some bytes",
        content_type="application/octet-stream",
    )
    assert response.status_code == 401
    assert response.json["msg"] == "Missing Authorization Header"
    mock_validate.assert_not_called()


def test_put_bam_too_large(authenticated_client, mocker):
    mocker.patch(
        "scimodom.api.attachment.get_valid_dataset", return_value=mocker.Mock()
    )
    mocker.patch(
        "scimodom.api.attachment.validate_dataset_write_permission", return_value=None
    )
    mocker.patch("scimodom.api.attachment.validate_request_size", return_value=None)
    mock_file_service = mocker.Mock()
    mock_file_service.create_or_update_bam_file.side_effect = FileTooLarge
    mocker.patch(
        "scimodom.api.attachment.get_file_service", return_value=mock_file_service
    )
    response = authenticated_client.put(
        "/d1/attachments/bams/name",
        data=b"some bytes",
        content_type="application/octet-stream",
    )
    assert response.status_code == 413
    assert response.json["message"] == "File too large (max. 2147483648 bytes)"


def test_deleted_bam_unauthenticated(unauthenticated_client, mocker):
    mock_validate = mocker.patch("scimodom.api.attachment.get_valid_dataset")
    response = unauthenticated_client.delete(
        "/d1/attachments/bams/name",
        data=b"some bytes",
        content_type="application/octet-stream",
    )
    assert response.status_code == 401
    assert response.json["msg"] == "Missing Authorization Header"
    mock_validate.assert_not_called()
