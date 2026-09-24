import logging
from smtplib import SMTPException

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    parse_valid_rna_type,
    validate_project_write_permission,
)
from scimodom.services.assembly import LiftOverError

from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.validator import (
    SelectionNotFoundError,
    DatasetImportError,
    DatasetHeaderError,
    DatasetExistsError,
    SpecsError,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.project import get_project_service
from scimodom.services.mail import get_mail_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.utils.importer.bed_importer import (
    BedImportTooManyErrors,
    BedImportEmptyFile,
)
from scimodom.utils.dtos.project import ProjectTemplate
from scimodom.utils.dtos.dataset import DatasetPostRequest

logger = logging.getLogger(__name__)

management_api = Blueprint("management_api", __name__)


@management_api.route("/project", methods=["POST"])
@cross_origin(supports_credentials=True)
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
            f"Request '{uuid}' created, but an unexpected error occurred "
            "during submission. Contact the system administrator.",
        )
    return {"message": "OK"}, 200
