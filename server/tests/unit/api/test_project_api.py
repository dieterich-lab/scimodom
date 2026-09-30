from smtplib import SMTPException

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

from scimodom.api.project import project_api


@pytest.fixture
def authenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(project_api, url_prefix="")
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
    app.register_blueprint(project_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def project_mocks(mocker):
    mock_project_service = mocker.Mock()
    mock_project_service.create_project_request.return_value = 123
    mocker.patch(
        "scimodom.api.project.get_project_service",
        return_value=mock_project_service,
    )
    mock_mail_service = mocker.Mock()
    mock_mail_service.send_project_request_notification.return_value = None
    mocker.patch(
        "scimodom.api.project.get_mail_service",
        return_value=mock_mail_service,
    )


def test_get_my_projects(unauthenticated_client):
    result = unauthenticated_client.get("/users/me/projects")
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"


def test_create_project_request(authenticated_client, mocker, project_mocks):
    mock_project_template = mocker.Mock()
    mocker.patch(
        "scimodom.api.project.ProjectTemplate.model_validate_json",
        return_value=mock_project_template,
    )
    result = authenticated_client.post("/projects/requests", json={"field": "value"})
    assert result.status_code == 200
    assert result.json["message"] == "OK"


def test_create_project_request_invalid_model(authenticated_client, project_mocks):
    result = authenticated_client.post("/projects/requests", json={})
    assert result.status_code == 400
    assert (
        result.json["message"]
        == "Request body validation: malformed and/or bad/missing fields"
    )


def test_create_project_request_invalid_json(authenticated_client, project_mocks):
    result = authenticated_client.post(
        "/projects/requests", data='{"title"}', content_type="application/json"
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
        "scimodom.api.project.get_project_service",
        return_value=mock_project_service,
    )
    mock_mail_service = mocker.Mock()
    mock_mail_service.send_project_request_notification.side_effect = SMTPException(
        "oups"
    )
    mocker.patch(
        "scimodom.api.project.get_mail_service",
        return_value=mock_mail_service,
    )
    mocker.patch(
        "scimodom.api.project.ProjectTemplate.model_validate_json",
        return_value=mocker.Mock(),
    )
    result = authenticated_client.post("/projects/requests", json={})
    assert result.status_code == 500
    assert result.json["message"] == "oups"
    assert (
        result.json["user_message"]
        == "Request '123' created, but an unexpected error occurred during submission. Contact our support team."
    )
    assert caplog.messages[0] == "Notification failed for project '123': oups"


def test_create_project_request_unauthenticated(unauthenticated_client, mocker):
    mock_project_service = mocker.patch("scimodom.api.project.get_project_service")
    result = unauthenticated_client.post("/projects/requests", json={"field": "value"})
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"
    mock_project_service.assert_not_called()
