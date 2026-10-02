import logging

import pytest
from flask import Flask, abort

from scimodom.api.helpers import register_error_handlers


@pytest.fixture
def app():
    app = Flask(__name__)
    # observe the handler, not the propagation
    app.config["PROPAGATE_EXCEPTIONS"] = False
    register_error_handlers(app)

    @app.get("/abort-405")
    def abort_405():
        abort(405)

    @app.get("/abort-500")
    def abort_500():
        abort(500)

    @app.get("/raise")
    def raise_error():
        raise RuntimeError("boom")

    return app


@pytest.fixture
def client(app):
    return app.test_client()


# tests


def test_http_exception_returns_standard_envelope(client):
    response = client.get("/abort-405")

    assert response.status_code == 405
    assert response.json["message"] == "Method Not Allowed"
    assert (
        response.json["user_message"]
        == "The method is not allowed for the requested URL."
    )


def test_http_exception_preserves_status_code(client, caplog):
    # i.e. not the handler's generic exception
    response = client.get("/abort-500")

    assert response.status_code == 500
    assert response.json["message"] == "Internal Server Error"
    assert (
        response.json["user_message"]
        == "The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application."
    )


def test_uncaught_exception_returns_500(client, caplog):
    with caplog.at_level(logging.ERROR):
        response = client.get("/raise")

    assert response.status_code == 500
    assert response.json["message"] == "Internal server error"
    assert response.json["user_message"] == (
        "An unexpected error occurred. Contact our support team "
        "if the problem persists."
    )
    assert caplog.messages[0] == "Unhandled exception while processing request: boom"
