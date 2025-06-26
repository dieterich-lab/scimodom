"""Provide error handlers."""

import logging

from flask import Flask
from werkzeug.exceptions import HTTPException

from .errors import create_error_response

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers.

    Standardize API error handling for unhandled
    Flask/Werkzeug and unexpected errors.

    NOTE: flask-jwt-extended authentication errors
    are not handled; they retain their native format
    {"msg": "..."}. The frontend already anticipates
    such cases where the backend might not cooperate.

    :param app: Flask app
    """

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error: HTTPException):
        status_code = error.code or 500
        return create_error_response(status_code, error.name, error.description)

    @app.errorhandler(Exception)
    def _handle_uncaught_exception(error: Exception):
        logger.exception(f"Unhandled exception while processing request: {error}")
        return create_error_response(
            500,
            "Internal server error",
            "An unexpected error occurred. Contact our support team "
            "if the problem persists.",
        )
