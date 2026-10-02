from flask import Blueprint

from scimodom.services.utilities import get_utilities_service

release_api = Blueprint("release_api", __name__)


@release_api.get("/info")
def get_release():
    """Get release, build, API information.

    :return: JSON object with info
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utitlies_service = get_utilities_service()
    return utitlies_service.get_release_info()
