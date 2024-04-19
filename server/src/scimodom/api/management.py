import logging
from smtplib import SMTPException

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.services.project import ProjectService
from scimodom.services.mail import get_mail_service
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)

management_api = Blueprint("management_api", __name__)


@management_api.route("/project", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def get_project():
    """Create a project request.

    NOTE: Users are not curently allowed to create
    projects, though this could be the case in the future,
    and only small changes would be required.
    """
    project_form = request.json
    try:
        uuid = ProjectService.create_project_request(project_form)
    except FileNotFoundError as exc:
        logger.error(f"Failed to save the project submission form: {exc}")
        return (
            jsonify(
                {
                    "result": "Failed to save the project submission form. Contact the administrator."
                }
            ),
            500,
        )

    mail_service = get_mail_service()
    try:
        mail_service.send_project_request_notification(uuid)
    except SMTPException as exc:
        logger.error(f"Failed to sent out notification email: {exc}")
        return (
            jsonify(
                {
                    "result": "Failed to sent out notification email. Contact the administrator."
                }
            ),
            500,
        )
    return jsonify({"result": "Ok"}), 200
