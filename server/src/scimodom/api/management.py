import logging
from pathlib import Path
from smtplib import SMTPException

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.api.helpers import create_error_response
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
from scimodom.services.annotation import RNA_TYPE_TO_ANNOTATION_SOURCE_MAP
from scimodom.services.project import get_project_service
from scimodom.services.mail import get_mail_service
import scimodom.utils.utils as utils
from scimodom.services.sunburst import get_sunburst_service
from scimodom.utils.importer.bed_importer import (
    BedImportTooManyErrors,
    BedImportEmptyFile,
)
from scimodom.utils.dtos.project import ProjectTemplate

logger = logging.getLogger(__name__)

management_api = Blueprint("management_api", __name__)


@management_api.route("/project", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def create_project_request():
    """Create a project request.

    Write a project template and inform
    the system administrator.
    """
    project_template_raw = request.data
    try:
        project_template = ProjectTemplate.model_validate_json(project_template_raw)
        project_service = get_project_service()
        uuid = project_service.create_project_request(project_template)
    except Exception as exc:
        logger.error(f"{exc}. The request was: {project_template_raw}.")
        raise exc

    mail_service = get_mail_service()
    try:
        mail_service.send_project_request_notification(uuid)
    except SMTPException as exc:
        logger.error(f"Project {uuid} saved, but failed to send out email: {exc}")
        message = (
            f"Request '{uuid}' created, but an error occurred during submission.\b"
            "Please contact the system administrator."
        )
        return create_error_response(500, message, message)
    return {"message": "OK"}, 200


@management_api.route("/dataset", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def add_dataset():
    """Add a new dataset to a project and import data.

    Parameter values are validated on import.
    """
    dataset_form = request.json
    annotation_source = RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[dataset_form["rna_type"]]
    upload_path = Path(get_config().UPLOAD_PATH, dataset_form["file_id"])
    dataset_service = get_dataset_service()
    try:
        with open(upload_path) as fp:
            dataset_service.import_dataset(
                fp,
                source=upload_path.as_posix(),
                smid=dataset_form["smid"],
                title=dataset_form["title"],
                assembly_id=dataset_form["assembly_id"],
                modification_ids=utils.to_list(dataset_form["modification_id"]),
                organism_id=dataset_form["organism_id"],
                technology_id=dataset_form["technology_id"],
                annotation_source=annotation_source,
            )
    except SelectionNotFoundError:
        return create_error_response(
            422,
            "Selection not found",
            "Invalid combination of RNA type, modification, organism, and/or technology.\n"
            "Modify the form to match a valid selection for this dataset.",
        )
    except DatasetImportError as e:
        message = str(e)
        logger.warning(
            f"DatasetImportError: {message}.\nThe request was: {dataset_form}."
        )
        return create_error_response(422, message, message)
    except DatasetHeaderError as e:
        message = str(e)
        return create_error_response(
            422,
            message,
            f"Inconsistent header: {message}\n"
            "Selected form values must agree with the file header.\n"
            "Modify the form or select the correct dataset to upload.",
        )
    except DatasetExistsError as e:
        message = str(e)
        return create_error_response(422, message, f"File upload failed: {message}")
    except SpecsError as e:
        message = str(e)
        return create_error_response(
            422,
            message,
            f"Invalid bedRMod format specifications: {message}\n"
            "Modify the file header to conform to the latest specifications.",
        )
    except BedImportEmptyFile as e:
        return create_error_response(
            422, str(e), "File upload failed. The file is empty."
        )
    except BedImportTooManyErrors as e:
        return create_error_response(
            422,
            str(e),
            f"File upload failed. Too many skipped records:\n{e.error_summary}\n"
            "Modify the file to conform to the latest bedRMod format specifications.\n"
            "Consult the documentation (Dataset upload errors) for more information.",
        )
    except LiftOverError as exc:
        return create_error_response(
            500, str(exc), "Liftover failed. Contact the system administrator."
        )
    except Exception as e:
        logger.error(
            f"Import failed in a unexpected way: {e}. The request was: {dataset_form}."
        )
        raise e
    sunburst_service = get_sunburst_service()
    sunburst_service.trigger_background_update()
    return {"result": "Ok"}, 200
