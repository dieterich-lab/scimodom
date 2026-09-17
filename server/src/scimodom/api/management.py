import logging
from pathlib import Path
from smtplib import SMTPException

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required
from pydantic import ValidationError

from scimodom.api.helpers import (
    parse_valid_rna_type,
    ClientResponseException,
    create_error_response,
)
from scimodom.config import get_config
from scimodom.services.assembly import LiftOverError

from scimodom.services.dataset import get_dataset_service
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
    :statuscode 400: Bad request - model validation failed
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


@management_api.route("/dataset", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def add_dataset():
    """Add new dataset to a project and import data.

    :param request: The incoming JSON request payload
    satisfying the DatasetPostRequest model
    :statuscode 200: OK
    :statuscode 400: Bad request - model validation
    :statuscode 401: Missing Authorization Header
    :statuscode 404: Not found - RNA type or selection
    :statuscode 422: Unprocessable Content - data validation
    :statuscode 500: Internal Server Error (or failed liftover)
    :statuscode 501: Not Implemented - RNA type annotation
    """
    dataset_service = get_dataset_service()
    try:
        dataset_form = DatasetPostRequest.model_validate_json(request.get_data())

        # MS14
        rna_type = parse_valid_rna_type(dataset_form.rna_type)
        annotation_source = AnnotationService.get_annotation_source(rna_type)

        upload_path = Path(get_config().UPLOAD_PATH, dataset_form.file_id)
        with open(upload_path) as fh:
            dataset_service.import_dataset(
                fh,
                source=upload_path.as_posix(),
                smid=dataset_form.smid,
                title=dataset_form.title,
                assembly_id=dataset_form.assembly_id,
                modification_ids=dataset_form.modification_id,
                organism_id=dataset_form.organism_id,
                technology_id=dataset_form.technology_id,
                annotation_source=annotation_source,
            )
    except ClientResponseException as exc:
        return exc.response_tuple
    except ValidationError:
        return create_error_response(
            400,
            "Request body validation: malformed and/or bad/missing fields",
        )
    except NotImplementedError:
        return create_error_response(
            501,
            f"rna_type '{rna_type}' not implemented",
        )
    except SelectionNotFoundError as exc:
        return create_error_response(
            404,
            str(exc),
            "Invalid combination of modification(s), organism, and/or technology.\n"
            "Modify the request form to match a valid selection for this dataset.\n"
            "Use GET /selections for valid combinations.",
        )
    except DatasetImportError as exc:
        return create_error_response(
            422,
            str(exc),
            "Modify the request form and re-submit",
        )
    except DatasetHeaderError as exc:
        return create_error_response(
            422,
            str(exc),
            "The request form must agree with the file header.\n"
            "Modify the request form or select the correct dataset to upload.",
        )
    except DatasetExistsError as exc:
        return create_error_response(422, str(exc))
    except SpecsError as exc:
        return create_error_response(
            422,
            str(exc),
            "Invalid bedRMod format specifications.\n"
            "Modify the file header to conform to the latest specifications.",
        )
    except BedImportEmptyFile as exc:
        return create_error_response(
            422, str(exc), "File upload failed. The file is empty."
        )
    except BedImportTooManyErrors as exc:
        return create_error_response(
            422,
            str(exc.error_summary),
            "Invalid bedRMod format specifications.\n"
            "Consult the documentation (Dataset upload errors) for more information.",
        )
    except LiftOverError as exc:
        return create_error_response(
            500, str(exc), "Liftover failed. Contact the system administrator."
        )

    sunburst_service = get_sunburst_service()
    sunburst_service.trigger_background_update()
    return {"message": "OK"}, 200
