import pytest
from flask import Flask
from io import BytesIO

from scimodom.api.upload import upload_api, MAX_TMP_FILE_SIZE
from scimodom.services.file import FileTooLarge


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(upload_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def mock_file_service(mocker):
    mock = mocker.Mock()
    mocker.patch(
        "scimodom.api.upload.get_file_service",
        return_value=mock,
    )
    return mock


def test_upload_tmp_file(test_client, mock_file_service):
    mock_file_service.upload_tmp_file.return_value = "abc123"

    response = test_client.post(
        "/uploads",
        data=b"some bytes",
        content_type="application/octet-stream",
    )

    assert response.status_code == 200
    assert response.get_json() == {"file_id": "abc123"}
    mock_file_service.upload_tmp_file.assert_called_once()
    # The service is called with the request stream and the max size.
    args, _ = mock_file_service.upload_tmp_file.call_args
    assert args[1] == MAX_TMP_FILE_SIZE


def test_upload_tmp_file_too_large_before(test_client, mock_file_service):
    response = test_client.post(
        "/uploads",
        data=b"x" * (MAX_TMP_FILE_SIZE + 1),
        content_type="application/octet-stream",
    )

    assert response.status_code == 413
    assert response.json["message"] == "File too large (max. 52428800 bytes)"
    mock_file_service.upload_tmp_file.assert_not_called()


def test_upload_tmp_file_too_large(test_client, mock_file_service):
    # when content_length is fake
    mock_file_service.upload_tmp_file.side_effect = FileTooLarge(MAX_TMP_FILE_SIZE)

    response = test_client.post(
        "/uploads",
        data=b"some bytes",
        content_type="application/octet-stream",
    )

    assert response.status_code == 413
    assert response.json["message"] == "File too large (max. 52428800 bytes)"
    mock_file_service.upload_tmp_file.assert_called_once()


def test_upload_tmp_file_falls_through(test_client, mock_file_service, mocker):
    # when content_length is none -> FileTooLarge should be raised
    # if not then this should go through
    mock_file_service.upload_tmp_file.return_value = "streamed123"
    mocker.patch(
        "scimodom.api.upload.request",
        new=mocker.Mock(content_length=None, stream=BytesIO(b"streamed")),
    )

    response = test_client.post(
        "/uploads",
        data=b"ignored",
        content_type="application/octet-stream",
    )

    assert response.status_code == 200
    assert response.get_json() == {"file_id": "streamed123"}
    mock_file_service.upload_tmp_file.assert_called_once()
