import pytest
from werkzeug.security import generate_password_hash

from scimodom.api.user import user_api
from scimodom.database.models import User, UserState
from scimodom.services.url import USER_API_ROUTE
from scimodom.services.user import UserService
from tests.api.schematise import validate, client_fixture

SCHEMA = "user.yaml"

client = client_fixture(user_api, USER_API_ROUTE)
auth_client = client_fixture(user_api, USER_API_ROUTE, authenticated=True)

CREDENTIALS = {"email": "ada@example.org", "password": "secret"}


@pytest.fixture
def services(Session, mocker):
    user_service = UserService(
        session=Session(),
        mail_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.user.get_user_service",
        return_value=user_service,
    )


def prefix_url(path: str) -> str:
    return f"{USER_API_ROUTE}{path}"


def test_register_schema(client, services):
    response = client.post(prefix_url("/users"), json=CREDENTIALS)
    validate(SCHEMA, response, 204)


def test_confirm_schema(client, Session, project, services):
    with Session() as session:
        user = User(
            email="ada@example.org",
            state=UserState.wait_for_confirmation,
            confirmation_token="t",
        )
        session.add(user)
        session.flush()

        response = client.post(
            prefix_url("/users/confirmation"),
            json={"email": "ada@example.org", "token": "t"},
        )
        validate(SCHEMA, response, 204)


def test_password_request_schema(client, project, services):
    response = client.post(
        prefix_url("/users/password/request"), json={"email": "contact@email"}
    )
    validate(SCHEMA, response, 204)


def test_password_reset_schema(client, Session, services):
    with Session() as session:
        user = User(
            email="ada@example.org",
            state=UserState.active,
            confirmation_token="t",
        )
        session.add(user)
        session.flush()
        response = client.post(
            prefix_url("/users/password/reset"), json={**CREDENTIALS, "token": "t"}
        )
        validate(SCHEMA, response, 204)


def test_me_schema(auth_client, project, services):
    response = auth_client.get(prefix_url("/users/me"))
    validate(SCHEMA, response, 200)


def test_my_password_schema(auth_client, project, services):
    response = auth_client.put(
        prefix_url("/users/me/password"), json={"password": "new"}
    )
    validate(SCHEMA, response, 204)


def test_login_schema(client, Session, services):
    with Session() as session:
        user = User(
            email="ada@example.org",
            state=UserState.active,
            password_hash=generate_password_hash("secret", method="pbkdf2"),
        )
        session.add(user)
        session.flush()
        response = client.post(prefix_url("/sessions"), json=CREDENTIALS)
        validate(SCHEMA, response, 200)


def test_refresh_schema(auth_client, services):
    response = auth_client.post(prefix_url("/sessions/refresh"))
    validate(SCHEMA, response, 200)
