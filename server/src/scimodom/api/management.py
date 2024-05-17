import logging
from smtplib import SMTPException

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.database.database import get_session
from scimodom.services.data import (
    DataService,
    InstantiationError,
    SelectionExistsError,
    DatasetExistsError,
    DatasetHeaderError,
)
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
    """Create a project request.

    NOTE: Users are not allowed to create projects,
    this must be done via requests. The project
    is created by the administrator, and the user is
    associated to the newly created project
    cf. "flask project" (cli.add_project)
    """
    project_form = request.json
    try:
        uuid = ProjectService.create_project_request(project_form)
    except FileNotFoundError as exc:
        logger.error(f"Failed to save the project submission form: {exc}")
        return (
            jsonify(
                {
                    "message": "Failed to save the project submission form. Contact the administrator."
                }
            ),
            500,
        )

    mail_service = get_mail_service()
    try:
        mail_service.send_project_request_notification(uuid)
    except SMTPException as exc:
        logger.error(f"Failed to send out notification email: {exc}")
        return (
            jsonify(
                {
                    "message": f"Project form successfully submitted, but failed to send out notification email. Contact the administrator with this ID: {uuid}."
                }
            ),
            500,
        )
    return jsonify({"message": "OK"}), 200


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
    try:
        data_service = DataService.from_new(
            get_session(),
            dataset_form["smid"],
            dataset_form["title"],
            dataset_form["path"],
            dataset_form["assembly_id"],
            modification_id=dataset_form["modification_id"],
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
            "message": "Invalid selection. Try again or contact the administrator."
        }, 422
    except Exception as exc:
        logger.error(f"{exc}. The request was: {dataset_form}.")
        return {"message": "Failed to create dataset. Contact the administrator."}, 500

    try:
        data_service.create_dataset()
    except DatasetHeaderError:
        return {
            "message": 'File upload failed. The file header does not match the value you entered for organism and/or assembly. Click "Cancel". Modify the form or the file header and start again.'
        }, 422
    except DatasetExistsError as exc:
        return {
            "message": f"File upload failed. {str(exc).replace('Aborting transaction!', '')} If you are unsure about what happened, click \"Cancel\" and contact the administrator."
        }, 422
    except EOFError as exc:
        return {"message": f"File upload failed. File {str(exc)} is empty!"}, 500
    except SpecsError as exc:
        return {
            "message": f"File upload failed. File is not conform to bedRMod specifications: {str(exc)}"
        }, 500

    except Exception as exc:
        # TODO ...
        logger.error(f"Failed to create dataset: {exc}")
        return (
            jsonify({"result": "Failed to upload dataset. Contact the administrator."}),
            500,
        )

    # TODO
    # WARNING scimodom.services.annotation.annotate_data.193 | No records found for Kr6uj7QzWfLJ...

    return jsonify({"result": "Ok"}), 200
