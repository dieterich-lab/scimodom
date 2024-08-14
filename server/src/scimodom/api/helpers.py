from pathlib import Path
import re
from typing import Optional

from flask import request, Response
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import NoResultFound
from pydantic import BaseModel

from scimodom.database.models import Dataset, User, BamFile
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import TargetsFileType, get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser
from scimodom.services.utilities import get_utilities_service
from scimodom.services.assembly import get_assembly_service
from scimodom.utils.common_dto import Strand

"""
This module supplies a number of helper functions to be used in various
API routes.

Incoming parameters validation

Each function gets a piece of unsafe data and returns an entity fetched
from the database or a cleaned, validated version of the input data.

A ClientResponseException is raised, which contains a data field
response_tupel, meant to be returned by a function handling a flask route.
This tuple will usually contain a dict, which will be turned by Flask
into a JSON document to form the body of the response and a HTTP status
code - usually a 4xx.

If something really unexpected happens, we leave it to Flask to generate
a 500 response. This module depends on Flask. Most importantly some
functions will assume that they are called while a HTTP request is
processed and use the Flask 'request'.

Response

Function to generate a response object, e.g. from a DTO.

"""

VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]{1,256}\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]{1,256}\Z")
INVALID_CHARS_REGEXP = re.compile(r"[^a-zA-Z0-9.,_-]")
MAX_DATASET_IDS_IN_LIST = 3


class ClientResponseException(Exception):
    def __init__(self, http_status: int, message: str):
        super(ClientResponseException, self).__init__(
            f"HTTP status {http_status} {message}"
        )
        self.response_tupel = {"message": message}, http_status


# Incoming parameter validation


def get_valid_dataset(dataset_id: str) -> Dataset:
    if not VALID_DATASET_ID_REGEXP.match(dataset_id):
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
        raise ClientResponseException(404, "Unknown file name")


def get_valid_dataset_id_list_from_request_parameter(parameter: str) -> list[str]:
    as_list = request.args.getlist(parameter, type=str)
    if len(as_list) > MAX_DATASET_IDS_IN_LIST:
        raise ClientResponseException(
            400,
            f"Parameter '{parameter} contained too many dataset IDs (max. {MAX_DATASET_IDS_IN_LIST})",
        )
    for dataset_id in as_list:
        if not VALID_DATASET_ID_REGEXP.match(dataset_id):
            raise ClientResponseException(
                400, f"Invalid dataset ID in parameter {parameter}"
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
        raise ClientResponseException(400, f"Invalid file ID in parameter {parameter}")
    file_service = get_file_service()
    if not file_service.check_tmp_upload_file_id(raw_id):
        raise ClientResponseException(
            404, "Temporary file not found - your upload may have expired"
        )
    return raw_id


def get_valid_remote_file_name_from_request_parameter(
    parameter: str, default: str = "uploaded file"
) -> Optional[str]:
    raw = request.args.get(parameter, type=str)
    if raw is None or raw == "":
        return default
    else:
        return re.sub(INVALID_CHARS_REGEXP, "?", raw)


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


def validate_request_size(max_size) -> None:
    if request.content_length is not None and request.content_length > max_size:
        raise ClientResponseException(413, f"File too large (max. {max_size} bytes)")


def get_valid_taxa_id(raw: str) -> int:
    utilities_service = get_utilities_service()
    taxa_ids = [d["id"] for d in utilities_service.get_taxa()]
    try:
        taxa_id = int(raw)
        if taxa_id not in taxa_ids:
            raise ClientResponseException(404, "Unrecognized Taxa ID")
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
    start = request.args.get("start", type=int)
    end = request.args.get("end", type=int)
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

    return (chrom, start, end, strand_dto)


def get_valid_logo(motif: str) -> Path:
    file_service = get_file_service()
    try:
        return file_service.get_motif_logo(motif)
    except FileNotFoundError:
        raise ClientResponseException(404, "Unknown motif")


# Response


def get_response_from_pydantic_object(obj: BaseModel):
    return Response(response=obj.json(), status=200, mimetype="application/json")
