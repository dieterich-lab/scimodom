import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from smtplib import SMTPException

from scimodom.api.user import user_api
from scimodom.services.user import UserExists, NoSuchUser, WrongUserOrPassword


@pytest.fixture
def unauthenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(user_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def authenticated_client():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(user_api, url_prefix="")
    client = app.test_client()
    with app.app_context():
        token = create_access_token(identity="test-user")
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    yield client


@pytest.mark.parametrize(
    "exception,http_status,msg,user_msg,log_msg",
    [
        (
            UserExists("User exists"),
            409,
            "User exists",
            "User already exists. Try to reset your password.",
            None,
        ),
        (
            SMTPException("Exception"),
            500,
            "Exception",
            "Failed to send registration email. Please verify your email address.\nIf the problem persists, contact our support team.",
            "Failed to send registration email: Exception",
        ),
    ],
)
def test_register_user_fail(
    unauthenticated_client,
    mocker,
    caplog,
    exception,
    http_status,
    msg,
    user_msg,
    log_msg,
):
    mock_user_service = mocker.Mock()
    mock_user_service.register_user.side_effect = exception
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=mock_user_service,
    )
    result = unauthenticated_client.post(
        "/users", json={"email": "user@email", "password": "pwd"}
    )
    assert result.status_code == http_status
    assert result.json["message"] == msg
    if user_msg is not None:
        assert result.json["user_message"] == user_msg
    if log_msg is not None:
        assert caplog.messages[0] == log_msg


def test_confirm_user_fail(
    unauthenticated_client,
    mocker,
):
    mock_user_service = mocker.Mock()
    mock_user_service.confirm_user.side_effect = WrongUserOrPassword
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=mock_user_service,
    )
    result = unauthenticated_client.post(
        "/users/confirmation", json={"email": "user@email", "token": "token123"}
    )
    assert result.status_code == 401
    assert result.json["message"] == "Invalid credentials"


@pytest.mark.parametrize(
    "exception,http_status,msg,user_msg,log_msg",
    [
        (
            NoSuchUser,
            404,
            "User 'user@email' not found",
            "User not found. Please verify your email address.\nIf the problem persists, contact our support team.",
            None,
        ),
        (
            SMTPException("Exception"),
            500,
            "Exception",
            "Failed to send email. Please verify your email address.\nIf the problem persists, contact our support team.",
            "Failed to send registration email: Exception",
        ),
    ],
)
def test_request_password_reset_fail(
    unauthenticated_client,
    mocker,
    caplog,
    exception,
    http_status,
    msg,
    user_msg,
    log_msg,
):
    mock_user_service = mocker.Mock()
    mock_user_service.request_password_reset.side_effect = exception
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=mock_user_service,
    )
    result = unauthenticated_client.post(
        "/users/password/request", json={"email": "user@email"}
    )
    assert result.status_code == http_status
    assert result.json["message"] == msg
    if user_msg is not None:
        assert result.json["user_message"] == user_msg
    if log_msg is not None:
        assert caplog.messages[0] == log_msg


def test_reset_password_fail(
    unauthenticated_client,
    mocker,
):
    mock_user_service = mocker.Mock()
    mock_user_service.do_password_reset.side_effect = WrongUserOrPassword
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=mock_user_service,
    )
    result = unauthenticated_client.post(
        "/users/password/reset",
        json={"email": "user@email", "password": "pw", "token": "token123"},
    )
    assert result.status_code == 401
    assert result.json["message"] == "Invalid credentials"


def test_login_fail(
    unauthenticated_client,
    mocker,
):
    mock_user_service = mocker.Mock()
    mock_user_service.check_password.return_value = False
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=mock_user_service,
    )
    result = unauthenticated_client.post(
        "/sessions",
        json={"email": "user@email", "password": "pw"},
    )
    assert result.status_code == 401
    assert result.json["message"] == "Invalid credentials"


def test_change_my_password(unauthenticated_client):
    result = unauthenticated_client.put("/users/me/password")
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"


def test_get_me(unauthenticated_client):
    result = unauthenticated_client.get("/users/me")
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"


def test_refresh_fail(unauthenticated_client):
    result = unauthenticated_client.post("/sessions/refresh")
    assert result.status_code == 401
    assert result.json["msg"] == "Missing Authorization Header"


def test_refresh(authenticated_client, mocker):
    mocker.patch(
        "scimodom.api.user.create_access_token",
        return_value="token123",
    )
    result = authenticated_client.post("/sessions/refresh")
    assert result.status_code == 200
    assert result.json["access_token"] == "token123"
