from flask import Blueprint, request, Response
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required

from scimodom.api.helpers import (
    get_validate_dataset,
    get_user_with_write_permission_on_dataset,
    get_valid_bam_file,
    ClientResponseException,
    validate_request_size,
)
from scimodom.services.file import get_file_service, FileTooLarge

bam_file_api = Blueprint("bam_file_api", __name__)

BUFFER_SIZE = 1024 * 1024
MAX_BAM_FILE_SIZE = 1024 * 1024 * 1024


@bam_file_api.route("/all/<dataset_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def list_bam_files(dataset_id: str):
    try:
        dataset = get_validate_dataset(dataset_id)
    except ClientResponseException as e:
        return e.response_tupel

    file_service = get_file_service()
    return file_service.get_bam_file_list(dataset)


@bam_file_api.route("/<dataset_id>/<name>", methods=["POST"])
@cross_origin(supports_credentials=True)
@jwt_required()
def post_bam_file(dataset_id: str, name: str):
    try:
        dataset = get_validate_dataset(dataset_id)
        _ = get_user_with_write_permission_on_dataset(dataset)
        validate_request_size(MAX_BAM_FILE_SIZE)
    except ClientResponseException as e:
        return e.response_tupel

    file_service = get_file_service()
    try:
        file_service.create_or_update_bam_file(
            dataset, name, request.stream, MAX_BAM_FILE_SIZE
        )
    except FileTooLarge:
        return {"message": f"File too large (max. {MAX_BAM_FILE_SIZE} bytes)"}, 413
    return {"message": "OK"}, 200


@bam_file_api.route("/<dataset_id>/<name>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_bam_file(dataset_id: str, name: str):
    try:
        dataset = get_validate_dataset(dataset_id)
        bam_file = get_valid_bam_file(dataset, name)
    except ClientResponseException as e:
        return e.response_tupel

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


@bam_file_api.route("/<dataset_id>/<name>", methods=["DELETE"])
@cross_origin(supports_credentials=True)
@jwt_required()
def delete_bam_file(dataset_id: str, name: str):
    try:
        dataset = get_validate_dataset(dataset_id)
        _ = get_user_with_write_permission_on_dataset(dataset)
        bam_file = get_valid_bam_file(dataset, name)
    except ClientResponseException as e:
        return e.response_tupel

    file_service = get_file_service()
    file_service.remove_bam_file(bam_file)
    return {"message": "OK"}, 200
