from flask import Blueprint

from scimodom.services.utilities import get_utilities_service

release_api = Blueprint("release_api", __name__)


@release_api.get("/releases")
def get_release():
    """Get release information.

    TODO: this function does not yet
    return what it should!

    :return: JSON object with summary
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utitlies_service = get_utilities_service()
    return utitlies_service.get_release_info()
