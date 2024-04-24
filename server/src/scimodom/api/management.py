import logging
from smtplib import SMTPException

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.database.database import get_session
from scimodom.services.dataset import DataService, InstantiationError
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
    """Add a new dataset to a project. Parameter
    values are validated by DataService. Project and
    assembly must exist.

    NOTE: Users are curently allowed to upload
    dataset to projects.
    """
    dataset_form = request.json
    session = get_session()
    try:
        data_service = DataService.from_new(
            session,
            dataset_form["smid"],
            dataset_form["title"],
            dataset_form["path"],
            dataset_form["assembly_id"],
            modification_id=dataset_form["modification_id"],
            technology_id=dataset_form["technology_id"],
            organism_id=dataset_form["organism_id"],
        )
    except InstantiationError as exc:
        logger.error(
            f"Failed to instantiate data service: {exc}. The form received was: {dataset_form}."
        )
        return (
            jsonify(
                {
                    "result": "Failed to create a dataset instance. Contact the administrator."
                }
            ),
            500,
        )

    data_service.create_dataset()
    # try:
    #     data_service.create_dataset()
    #     # TODO: feedback to user e.g. liftover, etc. and finally successful upload (return EUFID?)
    # except:
    #     # TODO: there are many exceptions ot handle
    #     logger.error(f"Failed to upload dataset ...")
    #     return (
    #         jsonify(
    #             {
    #                 "result": "Failed to upload dataset. Contact the administrator."
    #             }
    #         ),
    #         500,
    #     )

    # errors that can arise during creation
    # scimodom.services.dataset.DatasetError: Expected 9606 for organism; got 10090 (imported). Aborting transaction!
    # scimodom.services.dataset.DatasetError: Expected GRCm39 for assembly; got GRCm38 (imported). Aborting transaction!

    # logging
    # DEBUG scimodom.services.dataset.create_dataset.334 | Lifting over dataset from GRCm38 to GRCm39...
    # DEBUG scimodom.services.dataset.create_dataset.360 | Added dataset MALPJw5m5CWW to project gRHWaFYU with title = test upload 2, and the following associations: m6A:67. Annotating data now...
    # DEBUG scimodom.services.annotation.annotate_data.197 | Annotating records for EUFID MALPJw5m5CWW...

    return jsonify({"result": "Ok"}), 200
