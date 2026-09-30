import logging
from smtplib import SMTPException

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from scimodom.api.helpers import create_error_response
from scimodom.services.mail import get_mail_service
from scimodom.services.project import get_project_service
from scimodom.services.user import get_user_service
from scimodom.utils.dtos.project import ProjectTemplate

logger = logging.getLogger(__name__)

project_api = Blueprint("project_api", __name__)


@project_api.get("/projects")
def get_projects():
    """Get all projects.

    :return: JSON array with all available projects
    and related metadata.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return _get_projects()


@project_api.post("/projects/requests")
@jwt_required()
def create_project_request():
    """Create a project request and inform the administrator.

    :param request: The incoming JSON request payload
    satisfying the ProjecTemplate model
    :statuscode 200: OK
    :statuscode 400: Bad request - model validation
    :statuscode 401: Missing Authorization Header
    :statuscode 500: Internal Server Error (or failed notification)
    """
    project_service = get_project_service()
    mail_service = get_mail_service()
    try:
        project_template = ProjectTemplate.model_validate_json(request.get_data())
        uuid = project_service.create_project_request(project_template)
        mail_service.send_project_request_notification(uuid)
    except ValidationError:
        return create_error_response(
            400,
            "Request body validation: malformed and/or bad/missing fields",
        )
    except SMTPException as exc:
        logger.error(f"Notification failed for project '{uuid}': {exc}")
        return create_error_response(
            500,
            str(exc),
            f"Request '{uuid}' created, but an unexpected error occurred "
            "during submission. Contact our support team.",
        )
    return {"message": "OK"}, 200


@project_api.get("/users/me/projects")
@jwt_required()
def get_my_projects():
    """Get projects associated with user.

    :param header: The request header with current token.
    :return: JSON array with all available projects
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
    return _get_projects(user)


def _get_projects(user=None):
    project_service = get_project_service()
    projects = project_service.get_projects(user)
    for project in projects:
        for field in ["date_added", "date_published"]:
            if field in project and project[field] is not None:
                project[field] = project[field].timestamp()
    return projects
