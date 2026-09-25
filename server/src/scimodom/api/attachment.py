from flask import Blueprint, request, Response
from flask_jwt_extended import jwt_required

from scimodom.api.helpers import (
    get_valid_dataset,
    validate_dataset_write_permission,
    get_valid_bam_file,
    ClientResponseException,
    validate_request_size,
    create_file_too_large_response,
)
from scimodom.services.file import get_file_service, FileTooLarge

dataset_attachment_api = Blueprint("dataset_attachment_api", __name__)

BUFFER_SIZE = 1024 * 1024
MAX_BAM_FILE_SIZE = 2 * 1024 * 1024 * 1024


@dataset_attachment_api.get("/<dataset_id>/attachments/bams")
def list_bam_metadata(dataset_id: str):
    """Get metadata for BAM attachments for the given EUFID.

    :param dataset_id: Dataset identifier (EUFID)
    :return: JSON array with metadata for BAM attachments
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid dataset identifier
    :statuscode 404: Not Found - dataset identifier
    :statuscode 500: Internal Server Error
    """
    try:
        dataset = get_valid_dataset(dataset_id)
    except ClientResponseException as e:
        return e.response_tuple

    file_service = get_file_service()
    return file_service.get_bam_file_list(dataset)


@dataset_attachment_api.get("/<dataset_id>/attachments/bams/<name>")
def get_bam_file(dataset_id: str, name: str):
    """Download a BAM file attached to a dataset given by its identifier.

    :param dataset_id: Dataset identifier (EUFID)
    :param name: BAM file attachment name
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid dataset identifier
    or BAM name
    :statuscode 404: Not Found - dataset identifier or
    BAM name
    :statuscode 500: Internal Server Error
    """
    try:
        dataset = get_valid_dataset(dataset_id)
        bam_file = get_valid_bam_file(dataset, name)
    except ClientResponseException as e:
        return e.response_tuple

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


@dataset_attachment_api.put("/<dataset_id>/attachments/bams/<name>")
@jwt_required()
def put_bam_file(dataset_id: str, name: str):
    """Put a BAM file to a dataset given by its identifier.

    :param dataset_id: Dataset identifier (EUFID)
    :param name: BAM file attachment name
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid dataset identifier
    :statuscode 401: Missing Authorization Header
    :statuscode 403: Forbidden - dataset permission
    :statuscode 404: Not Found - dataset identifier
    :statuscode 413: Content Too Large
    :statuscode 422: Unprocessable Content - not enough segments
    or signature verification failed
    :statuscode 500: Internal Server Error
    """
    try:
        dataset = get_valid_dataset(dataset_id)
        validate_dataset_write_permission(dataset)
        validate_request_size(MAX_BAM_FILE_SIZE)
    except ClientResponseException as e:
        return e.response_tuple

    file_service = get_file_service()
    try:
        file_service.create_or_update_bam_file(
            dataset, name, request.stream, MAX_BAM_FILE_SIZE
        )
    except FileTooLarge:
        return create_file_too_large_response(MAX_BAM_FILE_SIZE)
    return {"message": "OK"}, 200


@dataset_attachment_api.delete("/<dataset_id>/attachments/bams/<name>")
@jwt_required()
def delete_bam_file(dataset_id: str, name: str):
    """Delete a BAM file attached to a dataset given by its identifier.

    :param dataset_id: Dataset identifier (EUFID)
    :param name: BAM file attachment name
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid dataset identifier
    or BAM name
    :statuscode 401: Missing Authorization Header
    :statuscode 403: Forbidden - dataset permission
    :statuscode 404: Not Found - dataset identifier or
    BAM name
    :statuscode 422: Unprocessable Content - not enough segments
    or signature verification failed
    :statuscode 500: Internal Server Error
    """
    try:
        dataset = get_valid_dataset(dataset_id)
        validate_dataset_write_permission(dataset)
        bam_file = get_valid_bam_file(dataset, name)
    except ClientResponseException as e:
        return e.response_tuple

    file_service = get_file_service()
    file_service.remove_bam_file(bam_file)
    return {"message": "OK"}, 200
