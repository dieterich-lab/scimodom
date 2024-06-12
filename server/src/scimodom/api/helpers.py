import re
from typing import Optional, List

from flask import request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.database.models import Dataset, User, BamFile
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser

"""
This module supplies a number of helper functions to be used in various
API routes. Each of them gets a piece of unsafe data coming for the
client or a hostile hacker. Most functions will return a entity fetched
from the database or a cleaned, validated version of the input data.

In case of an error they will raise a ClientResponseException, which
contains a data field response_tupel, meant to be returned by a function
handling a flask route. This tuple will usually contain a dict, which
will be turned by Flask into a JSON document to form the body of the
response and a HTTP status code - usually a 4xx.

In case of something really unexpected we leave it to Flask to generate
a 500 response. This module depends on Flask. Most importantly some
functions will assume that they are called while a HTTP request is
processed and use the Flask 'request'.
"""


class ClientResponseException(Exception):
    def __init__(self, http_status: int, message: str):
        super(ClientResponseException, self).__init__(
            f"HTTP status {http_status} {message}"
        )
        self.response_tupel = {"message": message}, http_status


VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]{1,256}\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]{1,256}\Z")
MAX_DATASET_IDS_IN_LIST = 3


def get_validate_dataset(dataset_id: str) -> Dataset:
    if not VALID_DATASET_ID_REGEXP.match(dataset_id):
        raise ClientResponseException(400, "Bad dataset ID")
    dataset_service = get_dataset_service()
    try:
        return dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        raise ClientResponseException(404, "Unknown dataset")


def get_user_with_write_permission_on_dataset(dataset) -> User:
    email = get_jwt_identity()
    user_service = get_user_service()
    permission_service = get_permission_service()

    try:
        user = user_service.get_user_by_email(email)
    except NoSuchUser:
        raise ClientResponseException(404, "Unknown user")
    if permission_service.may_change_dataset(user, dataset):
        return user
    else:
        raise ClientResponseException(401, "Not your dataset")


def get_valid_bam_file(dataset, name) -> BamFile:
    if not VALID_FILENAME_REGEXP.match(name):
        raise ClientResponseException(400, "Bad file name")
    file_service = get_file_service()
    try:
        return file_service.get_bam_file(dataset, name)
    except NoResultFound:
        raise ClientResponseException(404, "Unknown file name")


def get_valid_dataset_id_list_from_request_parameter(parameter: str) -> List[str]:
    as_list = request.args.getlist(parameter, type=str)
    if len(as_list) > MAX_DATASET_IDS_IN_LIST:
        raise ClientResponseException(
            400,
            f"Parameter '{parameter} contained too many dataset IDs (max. {MAX_DATASET_IDS_IN_LIST})",
        )
    for dataset_id in as_list:
        if not VALID_DATASET_ID_REGEXP.match(dataset_id):
            raise ClientResponseException(
                400, f"Bad dataset ID in parameter {parameter}"
            )
    return as_list


def get_valid_tmp_file_id_from_request_parameter(
    parameter: str, is_optional=False
) -> Optional[str]:
    raw_id = request.args.get(parameter, type=str)
    if raw_id is None or raw_id == "":
        if is_optional:
            return None
        raise ClientResponseException(400, f"Missing required parameter {parameter}")
    if not VALID_FILENAME_REGEXP.match(raw_id):
        raise ClientResponseException(400, f"Bad file ID in parameter {parameter}")
    file_service = get_file_service()
    if not file_service.check_tmp_upload_file_id(raw_id):
        raise ClientResponseException(
            404, "Temporary file not found - your upload may have expired"
        )
    return raw_id


def get_valid_boolean_from_request_parameter(
    parameter: str, default: Optional[bool] = None
) -> bool:
    raw_value = request.args.get(parameter, type=str)
    if raw_value is None:
        if default is None:
            raise ClientResponseException(
                400, f"Required parameter '{parameter} missing ('true' or 'false')"
            )
        else:
            return default
    lower_case_value = raw_value.lower()
    if lower_case_value == "false":
        return False
    if lower_case_value == "true":
        return True
    raise ClientResponseException(
        400, f"Got bad value for parameter '{parameter}' (allowed: 'true', 'false')"
    )


def validate_request_size(max_size):
    if request.content_length is not None and request.content_length > max_size:
        raise ClientResponseException(413, f"File too large (max. {max_size} bytes)")
