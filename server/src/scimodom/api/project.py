from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service


project_api = Blueprint("project_api", __name__)


@project_api.route("/list_all", methods=["GET"])
def list_all():
    return _get_projects_for_network()


def _get_projects_for_network(user=None):
    project_service = get_project_service()
    projects = project_service.get_projects(user)
    for project in projects:
        for field in ["date_added", "date_published"]:
            if field in project and project[field] is not None:
                project[field] = project[field].timestamp()
    return projects


@project_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    user_service = get_user_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return _get_projects_for_network(user)
