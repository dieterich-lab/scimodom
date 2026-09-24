from flask import Blueprint, request

from scimodom.api.helpers import create_file_too_large_response
from scimodom.services.file import get_file_service, FileTooLarge

upload_api = Blueprint("upload_api", __name__)

MAX_TMP_FILE_SIZE = 50 * 1024 * 1024


@upload_api.post("/uploads")
def upload_tmp_file():
    """Upload a temporary file.

    :statuscode 200: OK
    :statuscode 413: File too large
    :statuscode 500: Internal Server Error
    """
    if (
        request.content_length is not None
        and request.content_length > MAX_TMP_FILE_SIZE
    ):
        return create_file_too_large_response(MAX_TMP_FILE_SIZE)

    file_service = get_file_service()
    try:
        file_id = file_service.upload_tmp_file(request.stream, MAX_TMP_FILE_SIZE)
        return {"file_id": file_id}
    except FileTooLarge:
        return create_file_too_large_response(MAX_TMP_FILE_SIZE)
