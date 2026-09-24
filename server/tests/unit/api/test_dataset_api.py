import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from scimodom.api.dataset import dataset_api
from scimodom.services.assembly import LiftOverError
from scimodom.services.validator import (
    SpecsError,
    DatasetHeaderError,
    DatasetImportError,
    SelectionNotFoundError,
    DatasetExistsError,
)
from scimodom.utils.importer.bed_importer import (
    BedImportTooManyErrors,
    BedImportEmptyFile,
)


# @pytest.fixture
# def test_client():
#     app = Flask(__name__)
#     app.register_blueprint(dataset_api, url_prefix="")
#     yield app.test_client()


@pytest.fixture
def unauthenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(dataset_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def authenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(dataset_api, url_prefix="")
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="test-user")
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    yield client


@pytest.fixture
def dataset_mocks(mocker):
    mock_dataset_service = mocker.Mock()
    mock_dataset_service.import_dataset.return_value = None
    mocker.patch(
        "scimodom.api.dataset.get_dataset_service",
        return_value=mock_dataset_service,
    )
    mock_file_service = mocker.Mock()
    mock_file_service.check_tmp_upload_file_id.return_value = True
    mock_file_service.open_tmp_upload_file_by_id = mocker.mock_open()
    mocker.patch(
        "scimodom.api.dataset.get_file_service",
        return_value=mock_file_service,
    )
    mock_dataset_post_request = mocker.Mock()
    mock_dataset_post_request.file_id = "test.bed"
    mocker.patch(
        "scimodom.api.dataset.DatasetPostRequest.model_validate_json",
        return_value=mock_dataset_post_request,
    )
    mocker.patch(
        "scimodom.api.dataset.parse_valid_rna_type",
        return_value="any",
    )
    mocker.patch(
        "scimodom.api.dataset.AnnotationService.get_annotation_source",
        return_value=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.dataset.validate_project_write_permission",
        return_value=None,
    )
    mock_sunburst_service = mocker.Mock()
    mock_sunburst_service.trigger_background_update.return_value = None
    mocker.patch(
        "scimodom.api.dataset.get_sunburst_service",
        return_value=mock_sunburst_service,
    )
    yield mock_file_service


# tests


def test_get_my_datasets(unauthenticated_client):
    result = unauthenticated_client.get("/users/me/datasets")
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"


def test_add_dataset(authenticated_client, dataset_mocks):
    result = authenticated_client.post("/datasets", json={"field": "value"})
    assert result.status_code == 200
    assert result.json["message"] == "OK"


@pytest.mark.parametrize(
    "exception,http_status,msg,user_msg",
    [
        (ValueError, 422, "Rename the file and try to re-upload", None),
        (
            SelectionNotFoundError("Error"),
            404,
            "Error",
            "Invalid combination of modification(s), organism, and/or technology.\n"
            "Modify the request form to match a valid selection for this dataset.\n"
            "Use GET /selections for valid combinations.",
        ),
        (DatasetImportError, 422, "", "Modify the request form and re-submit"),
        (
            DatasetHeaderError,
            422,
            "",
            "The request form must agree with the file header.\n"
            "Modify the request form or select the correct dataset to upload.",
        ),
        (DatasetExistsError("Exists"), 422, "Exists", None),
        (
            SpecsError,
            422,
            "",
            "Invalid bedRMod format specifications.\n"
            "Modify the file header to conform to the latest specifications.",
        ),
        (BedImportEmptyFile, 422, "", "File upload failed. The file is empty."),
        (
            BedImportTooManyErrors("message", "error"),
            422,
            "error",
            "Invalid bedRMod format specifications.\n"
            "Consult the documentation (Dataset upload errors) for more information.",
        ),
        (
            LiftOverError,
            500,
            "",
            "Liftover failed. Contact the system administrator.",
        ),
    ],
)
def test_add_dataset_fail(
    authenticated_client, dataset_mocks, exception, http_status, msg, user_msg
):
    # use mock_file_service to parametrize side effects
    # we don't care who raises the exception
    mock = dataset_mocks
    mock.open_tmp_upload_file_by_id.side_effect = exception
    result = authenticated_client.post("/datasets", json={"field": "value"})
    assert result.status_code == http_status
    assert result.json["message"] == msg
    if user_msg is not None:
        assert result.json["user_message"] == user_msg


def test_add_dataset_file_not_found(authenticated_client, dataset_mocks):
    mock = dataset_mocks
    mock.check_tmp_upload_file_id.return_value = False
    result = authenticated_client.post("/datasets", json={"field": "value"})
    assert result.status_code == 404
    assert result.json["message"] == "File 'test.bed' not found"
    assert (
        result.json["user_message"] == "Select the file again and/or try to re-upload"
    )


def test_add_dataset_unauthenticated(unauthenticated_client, mocker):
    mock_validate = mocker.patch(
        "scimodom.api.dataset.DatasetPostRequest.model_validate_json"
    )
    result = unauthenticated_client.post("/datasets", json={"field": "value"})
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"
    mock_validate.assert_not_called()
