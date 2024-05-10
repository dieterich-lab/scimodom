import re

from flask import Blueprint, Response, stream_with_context, request
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.services.dataset import get_dataset_service
from scimodom.services.exporter import get_exporter, NoSuchDataset
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser

transfer_api = Blueprint("transfer_api", __name__)


VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]+\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]+\Z")


@transfer_api.route("/dataset/<dataset_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def export_dataset(dataset_id: str):
    exporter = get_exporter()
    try:
        file_name = exporter.get_dataset_file_name(dataset_id)
        return Response(
            stream_with_context(exporter.generate_dataset(dataset_id)),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except NoSuchDataset as exc:
        return {"message": str(exc)}, 404


@transfer_api.route("/bam_file/<dataset_id>/<name>", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def upload_bam_file(dataset_id: str, name: str):
    if not VALID_DATASET_ID_REGEXP.match(dataset_id):
        return {"message": "Bad dataset ID"}, 400
    if not VALID_FILENAME_REGEXP.match(name):
        return {"message": "Bad file name"}, 400
    email = get_jwt_identity()

    user_service = get_user_service()
    dataset_service = get_dataset_service()
    permission_service = get_permission_service()
    file_service = get_file_service()

    try:
        user = user_service.get_user_by_email(email)
    except NoSuchUser:
        return {"message": "Unknown user"}, 404
    try:
        dataset = dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        return {"message": "Unknown dataset"}, 404
    if not permission_service.may_attach_to_dataset(user, dataset):
        return {"message": "Not your dataset"}, 401

    file_service.create_or_update_bam_file(dataset, name, request.stream)
    return {"message": "OK"}, 200
