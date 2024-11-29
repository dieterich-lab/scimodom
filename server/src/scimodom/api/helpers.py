from pathlib import Path
import re
from typing import Optional, Any

from flask import request, Response
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import NoResultFound
from pydantic import BaseModel

from scimodom.database.models import Dataset, User, BamFile
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser
from scimodom.services.utilities import get_utilities_service
from scimodom.services.assembly import get_assembly_service
from scimodom.utils.specs.enums import Strand, TargetsFileType, Identifiers

"""
This module supplies a number of helper functions to be used in various
API routes.

Incoming parameters validation

Each function gets a piece of unsafe data and returns an entity fetched
from the database or a cleaned, validated version of the input data.

A ClientResponseException is raised, which contains a data field
response_tuple, meant to be returned by a function handling a flask route.
This tuple will usually contain a dict, which will be turned by Flask
into a JSON document to form the body of the response and a HTTP status
code - usually a 4xx. The response_tuple contains two items:

* A dict with the following keys:
  - message (mandatory): A short technical error message, which states
    the issue as precisely as possible assuming that the reader knows
    the all the context, especially the original HTTP request. This
    message is meant for debugging, logging or for users using the Rest
    API directly. The web frontend may fall back to use this message
    if no 'user_message' was supplied. In this case it is the
    responsibility of the frontend to add context information such as
    the operation, that failed, and the HTTP status code. That is the normal
    behaviour in case of a mismatch between frontend and backend, e.g. due
    to a bug, server failure, or network error.

  - user_message (optional): In case that the issue was caused by
    by user error (e.g. wrong password, bad email address) this field
    should be supplied. This message should contain all context the user
    may need to to understand the message. The frontend will usually display
    the message directly to the user without adding any context.
    It is pointless to supply this message in cases in which the
    the frontend validation will prevent the user error from reaching
    the backend. The user_message can *and* should be preformatted
    with line breaks at suitable spots.

* A HTTP error code - usually a 4xx if the problem on the frontend side,
  including all user errors, or 5xx in case the problem was most likely
  caused by the backend.

If something really unexpected happens, we leave it to Flask to generate
a 500 response. In this case the content of the response is a HTML document
without any details. This avoids information leak to hostile users (aka hackers).
Such issues must be tracked using the logs on the server side.

The helper functions in this modules mostly detect incorrect input
on the user side and generate mostly 4xx errors.

In addition a function create_error_response is supplied to allow modules
to generate a response in the same format without raising a
ClientResponseException.

This module depends on Flask. Most importantly some functions will assume
that they are called while a HTTP request is processed and use the Flask
'request' object.
"""

# EUFID length is validated separately
VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]{1,256}\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]{1,256}\Z")
INVALID_CHARS_REGEXP = re.compile(r"[^a-zA-Z0-9.,_-]")
MAX_DATASET_IDS_IN_LIST = 3


class ClientResponseException(Exception):
    """Extend base exception for client response."""

    def __init__(self, http_status: int, message: str, user_message: str | None = None):
        super(ClientResponseException, self).__init__(
            f"HTTP status {http_status} {message}"
        )
        self.response_tuple = create_error_response(http_status, message, user_message)


class FileTooLargeException(ClientResponseException):
    """Extend ClientResponseException for file size."""

    def __init__(self, max_size: int):
        message = _get_file_too_large_message(max_size)
        super(FileTooLargeException, self).__init__(413, message, message)


def create_error_response(
    status_code: int, message: str, user_message: str | None = None
) -> (dict[str, str], int):
    """Construct an error response.

    :param status_code: HTTP status code
    :type status_code: int
    :param message: General error message
    :type message: str
    :param user_message: Error message specifically for the user.
    This can be used e.g. to add context per endpoint, or
    intercept more complex error messages.
    :type error_message: str
    :returns: Error response
    :rtype: Tuple[dict[str, str], int]
    """
    json_response = {"message": message}
    if user_message is not None:
        json_response["user_message"] = user_message
    return json_response, status_code


def create_file_too_large_response(max_size: int) -> (dict[str, str], int):
    """Construct an error response for file size.

    :param max_size: Allowed max. file size
    :type max_size: int
    :returns: Error response
    :rtype: Tuple[dict[str, str], int]
    """
    message = _get_file_too_large_message(max_size)
    return create_error_response(413, message, message)


# Incoming parameter validation


def get_valid_dataset(dataset_id: str) -> Dataset:
    if not _is_valid_identifier(dataset_id, Identifiers.EUFID.length):
        raise ClientResponseException(400, "Invalid dataset ID")
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
        raise ClientResponseException(400, "Invalid file name")
    file_service = get_file_service()
    try:
        return file_service.get_bam_file(dataset, name)
    except NoResultFound:
        raise ClientResponseException(
            404, "Unknown file name and/or unknown/invalid dataset ID"
        )


def get_valid_dataset_id_list_from_request_parameter(parameter: str) -> list[str]:
    """Get a list of valid dataset IDs.

    :param parameter: Query parameter
    :type parameter: str
    :returns: List of dataset ID(s)
    :rtype: list[str]
    """
    as_list = get_unique_list_from_query_parameter(parameter, str)
    if len(as_list) > MAX_DATASET_IDS_IN_LIST:
        raise ClientResponseException(
            400,
            f"'{parameter}' contained too many dataset IDs (max. {MAX_DATASET_IDS_IN_LIST})",
        )
    dataset_service = get_dataset_service()
    for dataset_id in as_list:
        if not _is_valid_identifier(dataset_id, Identifiers.EUFID.length):
            raise ClientResponseException(400, f"Invalid dataset ID for '{parameter}'")
        try:
            dataset_service.get_by_id(dataset_id)
        except NoResultFound:
            raise ClientResponseException(404, f"Unknown dataset for '{parameter}'")
    return as_list


def get_valid_tmp_file_id_from_request_parameter(
    parameter: str, is_optional=False
) -> Optional[str]:
    """Get uploaded/temporary file identifier.

    :param parameter: Query parameter
    :type parameter: str
    :param is_optional: True if parameter is required (Default: False)
    :type is_optional: bool
    :returns: Uploaded/temporary file identifier or None
    :rtype: str | None
    """
    raw_id = request.args.get(parameter, type=str)
    if raw_id is None or raw_id == "":
        if is_optional:
            return None
        raise ClientResponseException(400, f"Missing required parameter '{parameter}'")
    if not VALID_FILENAME_REGEXP.match(raw_id):
        raise ClientResponseException(400, f"Invalid file ID in '{parameter}'")
    file_service = get_file_service()
    if not file_service.check_tmp_upload_file_id(raw_id):
        raise ClientResponseException(
            404,
            "Upload file ID not found",
            "File not found - Select the file again and try to re-upload",
        )
    return raw_id


def get_valid_remote_file_name_from_request_parameter(
    parameter: str, default: str = "uploaded file"
) -> str:
    """Get uploaded/temporary file name.

    :param parameter: Query parameter
    :type parameter: str
    :param default: Default file name
    :type default: str
    :returns: Uploaded/temporary file name
    :rtype: str | None
    """
    raw = request.args.get(parameter, type=str)
    if raw is None or raw == "":
        return default
    else:
        return re.sub(INVALID_CHARS_REGEXP, "?", raw)


def get_valid_boolean_from_request_parameter(
    parameter: str, default: Optional[bool] = None
) -> bool:
    """Get boolean value out of query parameter.

    :param parameter: Query parameter
    :type parameter: str
    :param default: Default value. If query
    parameter is None, and there is no default,
    a ClientResponseException is raised.
    :type default: bool | None
    :returns: Boolean value
    :rtype: bool
    """
    raw_value = request.args.get(parameter, type=str)
    if raw_value is None:
        if default is None:
            raise ClientResponseException(
                400, f"Required parameter '{parameter}' missing ('true' or 'false')"
            )
        else:
            return default
    lower_case_value = raw_value.lower()
    if lower_case_value == "false":
        return False
    if lower_case_value == "true":
        return True
    raise ClientResponseException(
        400, f"Invalid value for '{parameter}' (allowed: 'true', 'false')"
    )


def validate_request_size(max_size) -> None:
    if request.content_length is not None and request.content_length > max_size:
        message = f"File too large (max. {max_size} bytes)"
        raise FileTooLargeException(max_size)


def get_valid_taxa_id(is_optional: bool = False) -> Optional[int]:
    """Get Taxa ID from query parameter.

    :param is_optional: True if required (Default: False)
    :type is_optional: bool
    :returns: Taxa ID or None
    :rtype: int | None
    """
    taxa_id = request.args.get("taxaId", type=int)
    if taxa_id is None or taxa_id == "":
        if is_optional:
            return None
        raise ClientResponseException(400, "Invalid Taxa ID")
    _validate_taxa_id(taxa_id)
    return taxa_id


def get_valid_taxa_id_from_string(raw: str) -> int:
    try:
        taxa_id = int(raw)
        _validate_taxa_id(taxa_id)
        return taxa_id
    except ValueError:
        raise ClientResponseException(400, "Invalid Taxa ID")


def validate_rna_type(rna_type: str) -> None:
    utilities_service = get_utilities_service()
    valid_rna_types = [x["id"] for x in utilities_service.get_rna_types()]
    if rna_type not in valid_rna_types:
        raise ClientResponseException(404, "Unknown RNA type")


def get_valid_targets_type(raw: str) -> TargetsFileType:
    try:
        return TargetsFileType[raw]
    except KeyError:
        raise ClientResponseException(404, "Unknown targets type")


def get_valid_coords(taxa_id: int, context: int = 0) -> tuple[str, int, int, Strand]:
    chrom = request.args.get("chrom", type=str)
    if chrom is None:
        raise ClientResponseException(400, "Invalid chrom")
    start = request.args.get("start", type=int)
    if start is None:
        raise ClientResponseException(400, "Invalid start")
    end = request.args.get("end", type=int)
    if end is None:
        raise ClientResponseException(400, "Invalid end")
    strand = request.args.get("strand", default=".", type=str)

    assembly_service = get_assembly_service()
    chroms = assembly_service.get_chroms(taxa_id)
    if chrom not in [d["chrom"] for d in chroms]:
        raise ClientResponseException(
            404, f"Unrecognized chrom '{chrom}' for Taxa '{taxa_id}'"
        )
    if not start < end:
        raise ClientResponseException(
            400, "Invalid coordinates: start must be smaller than end"
        )
    chrom_size = [d for d in chroms if d["chrom"] == chrom][0]["size"]
    if not end < chrom_size:
        raise ClientResponseException(
            400, "Invalid coordinates: end is greater than chrom size"
        )
    try:
        strand_dto = Strand(strand)
    except ValueError:
        raise ClientResponseException(400, "Invalid strand value")

    if context > 0:
        start = start - context
        if start < 0:
            start = 0
        end = end + context
        if end > chrom_size:
            end = chrom_size

    return chrom, start, end, strand_dto


def get_valid_logo(motif: str) -> Path:
    file_service = get_file_service()
    try:
        return file_service.get_motif_logo(motif)
    except FileNotFoundError:
        raise ClientResponseException(404, "Unknown motif")


def get_non_negative_int(field: str) -> int:
    raw = request.args.get(field, type=int)
    if raw is None or raw < 0:
        raise ClientResponseException(400, f"Invalid {field}")
    return raw


def get_positive_int(field: str) -> int:
    raw = request.args.get(field, type=int)
    if raw is None or raw <= 0:
        raise ClientResponseException(400, f"Invalid {field}")
    return raw


def get_optional_non_negative_int(field: str) -> int | None:
    raw = request.args.get(field, type=int)
    if raw is None:
        return None
    if raw < 0:
        raise ClientResponseException(400, f"Invalid {field}")
    return raw


def get_optional_positive_int(field: str) -> int | None:
    raw = request.args.get(field, type=int)
    if raw is None:
        return None
    if raw <= 0:
        raise ClientResponseException(400, f"Invalid {field}")
    return raw


def get_unique_list_from_query_parameter(name: str, list_type) -> list[Any]:
    """Get unique list from query parameters.

    There seem to be some confusion how arrays should be transmitted
    as query parameters. While most people seem to agree that the values
    are packed into multiple query parameters, some (older?) implementations
    leave the original name, while newer ones insist on adding square
    brackets '[]' at the end of the name, e.g. my_array = ['x', 'y'] may be
    transmitted like this:

        Old: ?my_array=x&my_array=y
        New: ?my_array[]=x&my_array[]=y

    Flask seems not to be aware of this. We don't care and allow both.
    Also, we don't want that our code breaks if Flask fixes this - so we
    ignore double results. So don't use this function for lists that are
    allowed to contain the same value multiple times. Note also that the
    order of returned values is not guaranteed.
    """
    result_as_set = {
        *request.args.getlist(name, type=list_type),
        *request.args.getlist(f"{name}[]", type=list_type),
    }
    return list(result_as_set)


# Response


def get_response_from_pydantic_object(obj: BaseModel):
    return Response(
        response=obj.model_dump_json(), status=200, mimetype="application/json"
    )


# Private


def _get_file_too_large_message(max_size: int):
    return f"File too large (max. {max_size} bytes)"


def _is_valid_identifier(identifier, length):
    if not VALID_DATASET_ID_REGEXP.match(identifier):
        return False
    elif len(identifier) != length:
        return False
    return True


def _validate_taxa_id(taxa_id: int) -> None:
    utilities_service = get_utilities_service()
    taxa_ids = [d["id"] for d in utilities_service.get_taxa()]
    if taxa_id not in taxa_ids:
        raise ClientResponseException(404, "Unrecognized Taxa ID")
