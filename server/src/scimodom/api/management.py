import logging
from pathlib import Path
from smtplib import SMTPException

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.config import Config
from scimodom.database.database import get_session
from scimodom.services.assembly import LiftOverError
from scimodom.services.data import (
    DataService,
    InstantiationError,
    SelectionExistsError,
    DatasetExistsError,
    DatasetHeaderError,
)
from scimodom.services.importer.base import MissingDataError
from scimodom.services.importer.header import SpecsError
from scimodom.services.project import ProjectService
from scimodom.services.mail import get_mail_service
import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)

management_api = Blueprint("management_api", __name__)


@management_api.route("/project", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def create_project_request():
    """Create a project request: write a project
    template and inform the system administrator.

    NOTE: Users are not allowed to create projects.
    """
    project_form = request.json
    try:
        uuid = ProjectService.create_project_request(project_form)
    except Exception as exc:
        logger.error(f"{exc}. The request was: {project_form}.")
        return {
            "message": "Failed to create request. Contact the system administrator."
        }, 500

    mail_service = get_mail_service()
    try:
        mail_service.send_project_request_notification(uuid)
    except SMTPException as exc:
        logger.error(f"Project {uuid} saved, but failed to send out email: {exc}")
        return {
            "message": f"An error occurred during submission. Your submission ID is {uuid}. Contact the system administrator."
        }, 500
    return {"message": "OK"}, 200


@management_api.route("/dataset", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def add_dataset():
    """Add a new dataset to a project and import data.
    Parameter values are validated by DataService.

    NOTE: Permissions are not handled here. The
    SMID in the dataset form is coming from
    one of the "allowed" projects for this user, i.e.
    the user is only able to select from his own projects.
    """
    dataset_form = request.json
    upload_path = Path(Config.UPLOAD_PATH, dataset_form["file_id"])
    try:
        data_service = DataService.from_options(
            get_session(),
            dataset_form["smid"],
            dataset_form["title"],
            upload_path,
            dataset_form["assembly_id"],
            modification_ids=dataset_form["modification_id"],
            technology_id=dataset_form["technology_id"],
            organism_id=dataset_form["organism_id"],
        )
    except SelectionExistsError:
        return {
            "message": "Invalid combination of RNA type, modification, organism, and/or technology. Modify the form and try again."
        }, 422
    except InstantiationError as exc:
        logger.error(f"{exc}. The request was: {dataset_form}.")
        return {
            "message": "Invalid selection. Try again or contact the system administrator."
        }, 422
    except Exception as exc:
        logger.error(f"{exc}. The request was: {dataset_form}.")
        return {
            "message": "Failed to create dataset. Contact the system administrator."
        }, 500

    try:
        data_service.create_dataset()
    except DatasetHeaderError:
        return {
            "message": 'File upload failed. Mismatch for organism and/or assembly between the file header and the selected values. Click "Cancel". Modify the form or the file and start again.'
        }, 422
    except DatasetExistsError as exc:
        return {
            "message": f"File upload failed. {str(exc).replace('Aborting transaction!', '')} If you are unsure about what happened, click \"Cancel\" and contact the system administrator."
        }, 422
    except EOFError as exc:
        return {"message": f"File upload failed. File {str(exc)} is empty!"}, 500
    except SpecsError as exc:
        return {
            "message": f"File upload failed. The header is not conform to bedRMod specifications: {str(exc)}"
        }, 500
    except MissingDataError:
        return {"message": "File upload failed. Too many skipped records."}, 500
    except LiftOverError:
        return {
            "message": "Liftover failed. Check your data, or contact the system administrator."
        }, 500
    except Exception as exc:
        logger.error(exc)
        return {"message": "File upload failed. Contact the system administrator."}, 500

    return {"result": "Ok"}, 200
