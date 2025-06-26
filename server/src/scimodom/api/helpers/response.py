"""Provide HTTP responses."""

from flask import Response
from pydantic import BaseModel


def get_response_from_pydantic_object(
    obj: BaseModel,
    status: int = 200,
) -> Response:
    """Dump a model to a Flask response object.

    :param obj: A pydantic object
    :param status: HTTP status code to return
    :return: The Flask response with the jsonified model
    """
    return Response(
        response=obj.model_dump_json(),
        status=status,
        mimetype="application/json",
    )
