"""Read and check an OpenAPI schema against its API response.

The OpenAPI definitions must be generated from the fragments
beforehand as in the Sphinx build:

    python docs/source/include_swagger_api_spec.py

The tests only read the merged files (docs/source/openapi/_include).

A request is never generated from a schema definition, this must be
done in each test. Only documented routes with OpenAPI definitions
are tested (per-endpoint tests have to be maintained).

Catches schema violations, validation gaps, and, up to mocks,
server errors.
"""

from functools import cache
from pathlib import Path

import pytest
import yaml
from flask import Flask
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager, create_access_token
from flask import Blueprint
from openapi_core import Config, OpenAPI
from openapi_core.contrib.werkzeug import (
    WerkzeugOpenAPIRequest,
    WerkzeugOpenAPIResponse,
)

from scimodom.services.url import API_PREFIX
from scimodom.api.helpers.serialisation import set_json_provider

SERVER_DIR = Path(__file__).parents[2]
OPENAPI_DIR = SERVER_DIR / "docs" / "source" / "openapi"
INCLUDE_DIR = OPENAPI_DIR / "_include"


class _ResponseOnlyRequest(WerkzeugOpenAPIRequest):
    @property
    def body(self) -> bytes:
        return b""


@cache
def _spec_dir() -> Path:
    merged = sorted(INCLUDE_DIR.glob("*.yaml"))
    if not merged:
        pytest.fail(f"No OpenAPI specs: '{INCLUDE_DIR}'")
    fragments = list(OPENAPI_DIR.glob("*.yaml"))
    if max(f.stat().st_mtime for f in fragments) > min(
        m.stat().st_mtime for m in merged
    ):
        pytest.fail("Stale OpenAPI specs")
    return INCLUDE_DIR


@cache
def _load_spec(schema: str) -> dict:
    spec = yaml.safe_load((_spec_dir() / schema).read_text())
    spec["servers"] = [{"url": f"/{API_PREFIX}"}]
    return spec


@cache
def create_openapi(schema: str) -> OpenAPI:
    """Create an OpenAPI from a definition."""
    config = Config(
        extra_media_type_deserializers={
            "text/csv": lambda data: data.decode(),
            "application/octet-stream": lambda data: data,
        }
    )
    return OpenAPI.from_dict(_load_spec(schema), config=config)


def validate(schema: str, response, status: int | None = None) -> None:
    """Validate the given response object associated with the request."""
    if status is not None:
        assert response.status_code == status
    create_openapi(schema).validate_response(
        _ResponseOnlyRequest(response.request),
        WerkzeugOpenAPIResponse(response),
    )


# fixtures


def make_client(
    blueprint: Blueprint, prefix: str, *, authenticated: bool = False
) -> FlaskClient:
    """Provide a test client mounted at its production URL prefix."""
    app = Flask(__name__)
    set_json_provider(app)
    app.config["JWT_SECRET_KEY"] = "test-secret"
    JWTManager(app)
    app.register_blueprint(blueprint, url_prefix=prefix)
    client = app.test_client()
    if authenticated:
        with app.app_context():
            token = create_access_token(identity="contact@email")
        client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client


def client_fixture(blueprint: Blueprint, prefix: str, *, authenticated: bool = False):
    """Make a pytest fixture yielding make_client(...)."""

    @pytest.fixture
    def _client():
        yield make_client(blueprint, prefix, authenticated=authenticated)

    return _client
