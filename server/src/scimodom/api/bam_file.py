import re

from flask import Blueprint, request, Response
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service, FileTooLarge
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser

bam_file_api = Blueprint("bam_file_api", __name__)

VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]+\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]+\Z")

BUFFER_SIZE = 1024 * 1024
MAX_BAM_FILE_SIZE = 2  # 1024 * 1024 * 1024


@bam_file_api.route("/all/<dataset_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def list_bam_files(dataset_id: str):
    dataset, error, status = _get_dataset_or_error(dataset_id)
    if dataset is None:
        return {"message": error}, status

    file_service = get_file_service()
    return file_service.get_bam_file_list(dataset)


def _get_dataset_or_error(dataset_id):
    if not VALID_DATASET_ID_REGEXP.match(dataset_id):
        return None, "Bad dataset ID", 400
    dataset_service = get_dataset_service()
    try:
        return dataset_service.get_by_id(dataset_id), None, None
    except NoResultFound:
        return None, "Unknown dataset", 404


@bam_file_api.route("/<dataset_id>/<name>", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def post_bam_file(dataset_id: str, name: str):
    dataset, error, status = _get_dataset_or_error(dataset_id)
    if dataset is None:
        return {"message": error}, status
    user, error, status = _get_user_with_write_permission_or_error(dataset)
    if user is None:
        return {"message": error}, status
    if (
        request.content_length is not None
        and request.content_length > MAX_BAM_FILE_SIZE
    ):
        return {"message": f"File too large (max. {MAX_BAM_FILE_SIZE} bytes)"}, 413

    file_service = get_file_service()
    try:
        file_service.create_or_update_bam_file(
            dataset, name, request.stream, MAX_BAM_FILE_SIZE
        )
    except FileTooLarge:
        return {"message": f"File too large (max. {MAX_BAM_FILE_SIZE} bytes)"}, 413
    return {"message": "OK"}, 200


def _get_user_with_write_permission_or_error(dataset):
    email = get_jwt_identity()
    user_service = get_user_service()
    permission_service = get_permission_service()

    try:
        user = user_service.get_user_by_email(email)
    except NoSuchUser:
        return None, "Unknown user", 404

    if permission_service.may_change_dataset(user, dataset):
        return user, None, None
    else:
        return False, "Not your dataset", 401


@bam_file_api.route("/<dataset_id>/<name>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_bam_file(dataset_id: str, name: str):
    dataset, error, status = _get_dataset_or_error(dataset_id)
    if dataset is None:
        return {"message": error}, status
    bam_file, error, status = _get_bam_file_or_error(dataset, name)
    if bam_file is None:
        return {"message": error}, status

    file_service = get_file_service()

    def generate():
        with file_service.open_bam_file(bam_file) as fp:
            while True:
                buffer = fp.read(BUFFER_SIZE)
                if len(buffer) == 0:
                    break
                yield buffer

    return Response(
        generate(),
        mimetype="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{bam_file.original_file_name}"'
        },
    )


def _get_bam_file_or_error(dataset, name):
    if not VALID_FILENAME_REGEXP.match(name):
        return None, "Bad file name", 400
    file_service = get_file_service()
    try:
        return file_service.get_bam_file(dataset, name), None, None
    except NoResultFound:
        return None, "Unknown file name", 404


@bam_file_api.route("/<dataset_id>/<name>", methods=["DELETE"])
@cross_origin(supports_credentials=True)
@jwt_required()
def delete_bam_file(dataset_id: str, name: str):
    dataset, error, status = _get_dataset_or_error(dataset_id)
    if dataset is None:
        return {"message": error}, status
    user, error, status = _get_user_with_write_permission_or_error(dataset)
    if user is None:
        return {"message": error}, status
    bam_file, error, status = _get_bam_file_or_error(dataset, name)
    if bam_file is None:
        return {"message": error}, status

    file_service = get_file_service()
    file_service.remove_bam_file(bam_file)
    return {"message": "OK"}, 200
