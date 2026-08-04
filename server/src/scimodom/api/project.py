from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service


project_api = Blueprint("project_api", __name__)


@project_api.route("/list_all", methods=["GET"])
def list_all():
    """Get all projects.

    :returns: JSON array with all available projects
    and related metadata.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return _get_projects_for_network()


@project_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    """Get project associated with user.

    This endpoint is restricted to authenticated users.
    A call to "get_user_by_email" may raise a "NoSuchUser"
    exception, but this should not happen in practice.
    If it does, it will be caught by the 500.

    :param header: The request header with current token.
    :returns: JSON array with all available projects
    and related metadata.
    :statuscode 200: OK
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return _get_projects_for_network(user)


def _get_projects_for_network(user=None):
    project_service = get_project_service()
    projects = project_service.get_projects(user)
    for project in projects:
        for field in ["date_added", "date_published"]:
            if field in project and project[field] is not None:
                project[field] = project[field].timestamp()
    return projects
