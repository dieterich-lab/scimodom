import logging
from pathlib import Path

from flask import Blueprint, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from scimodom.config import Config
from scimodom.services.comparison import (
    get_comparison_service,
    FailedUploadError,
    NoRecordsFoundError,
)
from scimodom.services.dataset import get_dataset_service
from scimodom.services.user import get_user_service

logger = logging.getLogger(__name__)

dataset_api = Blueprint("dataset_api", __name__)


@dataset_api.route("/list_all", methods=["GET"])
def list_all():
    dataset_service = get_dataset_service()
    return dataset_service.get_datasets()


@dataset_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    user_service = get_user_service()
    dataset_service = get_dataset_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return dataset_service.get_datasets(user)


@dataset_api.route("/compare", methods=["GET"])
@cross_origin(supports_credentials=True)
def compare():
    """Compare dataset (Compare View)."""

    def is_true(value):
        return value.lower() == "true"

    reference_ids = request.args.getlist("reference", type=str)
    comparison_ids = request.args.getlist("comparison", type=str)
    upload_id = request.args.get("upload", type=str)
    operation = request.args.get("operation", type=str)
    is_strand = request.args.get("strand", type=is_true)
    is_euf = request.args.get("euf", type=is_true)

    comparison_service = get_comparison_service(operation, is_strand)
    if upload_id:
        try:
            upload_path = Path(Config.UPLOAD_PATH, upload_id)
            comparison_service.upload_records(upload_path, is_euf)
        except FailedUploadError as exc:
            logger.error(f"Failed upload (Comparison): {exc}")
            return {
                "message": "File upload failed. Contact the system administrator."
            }, 500
        except NoRecordsFoundError:
            return {
                "message": (
                    "File upload failed. No records were found. Allowed formats are BED6 or bedRMod. "
                    "For more information, consult the documentation."
                )
            }, 500
    else:
        comparison_service.query_comparison_records(comparison_ids)

    comparison_service.query_reference_records(reference_ids)
    try:
        return comparison_service.compare_dataset()
    except Exception as exc:
        logger.error(f"Failed comparison: {exc}")
        return {
            "message": (
                "Failed to compare dataset. The server encountered an unexpected error. "
                "Contact the system administrator."
            )
        }, 500
