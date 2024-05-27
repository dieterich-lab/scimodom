from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service


project_api = Blueprint("project_api", __name__)


@project_api.route("/list_all", methods=["GET"])
def list_all():
    project_service = get_project_service()
    return project_service.get_projects()


@project_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    user_service = get_user_service()
    project_service = get_project_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return project_service.get_projects(user)
