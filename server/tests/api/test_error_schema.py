from pathlib import Path

import pytest
import yaml
from flask import Flask
from openapi_schema_validator import OAS30Validator

from scimodom.api.helpers import ClientResponseException, register_error_handlers
from scimodom.api.helpers.serialisation import set_json_provider

COMMON = Path(__file__).parents[2] / "docs" / "source" / "openapi" / "_common.yaml"
ERROR = yaml.safe_load(COMMON.read_text())["components"]["schemas"]["Error"]


def validate_error(response, status):
    assert response.status_code == status
    assert response.is_json
    OAS30Validator(ERROR).validate(response.json)


@pytest.fixture
def app():
    app = Flask(__name__)
    set_json_provider(app)
    register_error_handlers(app)  # the real handlers

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    @app.post("/post-only")
    def post_only():
        return {}

    @app.get("/client-error")
    def client_error():
        try:
            raise ClientResponseException(400, "Bad value", "Please fix it")
        except ClientResponseException as exc:
            return exc.response_tuple

    return app


@pytest.mark.parametrize(
    "url, status",
    [("/missing", 404), ("/post-only", 405), ("/boom", 500), ("/client-error", 400)],
)
def test_error_schema_handlers(app, url, status):
    validate_error(app.test_client().get(url), status)


def test_the_check_is_not_vacuous():
    with pytest.raises(Exception):
        OAS30Validator(ERROR).validate({"msg": "jwt format"})  # no 'message'
