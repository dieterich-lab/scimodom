import re
from typing import Optional, Any, TypeVar
from collections.abc import Callable

from flask import request, Response
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import NoResultFound
from pydantic import BaseModel

from scimodom.services.annotation import get_annotation_service
from scimodom.database.models import Dataset, User, BamFile
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import get_user_service, NoSuchUser
from scimodom.services.utilities import get_utilities_service
from scimodom.services.assembly import get_assembly_service
from scimodom.utils.specs.enums import (
    Strand,
    TargetsFileType,
    Identifiers,
    SunburstChartType,
)

"""
NOTE: Most functions exposed in this module must be called while
a HTTP request is processed and use the Flask 'request' object.
"""


T = TypeVar("T")  # Callable return type

# EUFID length is validated separately
VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]{1,256}\Z")
VALID_FILENAME_REGEXP = re.compile(r"\A[a-zA-Z0-9.,_-]{1,256}\Z")
INVALID_CHARS_REGEXP = re.compile(r"[^a-zA-Z0-9.,_-]")
MAX_DATASET_IDS_IN_LIST = 3


class ClientResponseException(Exception):
    """Extend the base exception for a client response.

    The message is meant for debugging, logging or for users
    using the REST API directly. The web frontend may fall back
    to use this message if no 'user_message' was supplied, in which
    case it is the responsibility of the frontend to add context.

    The user_message (optional) is mostly intended for user errors
    (e.g. wrong password, bad email address). This message should
    add context; the frontend will usually display it directly to
    the user without adding any context. The user_message should
    be formatted.
    """

    def __init__(
        self,
        http_status: int,
        message: str,
        user_message: str | None = None,
    ):
        super(ClientResponseException, self).__init__(
            f"HTTP status {http_status} {message}"
        )
        self.response_tuple = create_error_response(
            http_status,
            message,
            user_message,
        )


class FileTooLargeException(ClientResponseException):
    """Extend ClientResponseException for file size."""

    def __init__(self, max_size: int):
        message = _get_file_too_large_message(max_size)
        super(FileTooLargeException, self).__init__(413, message, message)


def create_error_response(
    status_code: int, message: str, user_message: str | None = None
) -> tuple[dict[str, str], int]:
    """Construct an error response.

    This function allows to generate a response in the same
    format without raising a ClientResponseException.

    :param status_code: HTTP status code
    :param message: General error message
    :param user_message: Error message specifically for the user.
    :return: Error response tuple
    """
    json_response = {"message": message}
    if user_message is not None:
        json_response["user_message"] = user_message
    return json_response, status_code


def create_file_too_large_response(max_size: int) -> tuple[dict[str, str], int]:
    """Construct an error response for file size.

    :param max_size: Allowed max. file size
    :return: Error response
    """
    message = _get_file_too_large_message(max_size)
    return create_error_response(413, message, message)


def _get_file_too_large_message(max_size: int):
    return f"File too large (max. {max_size} bytes)"


# Request body validation


def get_required_json_fields(*fields: str) -> dict[str, Any]:
    """Validate JSON object, i.e. if it contains given fields.

    This function does not perform field validation.

    :params fields: JSON fields
    :return: The valid JSON request body
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ClientResponseException(400, "Request body must be a JSON object")
    missing = [field for field in fields if field not in body]
    if missing:
        raise ClientResponseException(
            400, f"Missing required field(s): {', '.join(missing)}"
        )
    return body


# Incoming (query or route) parameter validation

# - Type conversion and syntax validation
# - Semantic validation must be performed by the caller


def get_non_negative_int(name: str) -> int:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _get_required_query_param(name, _non_negative_int, "integer")


def get_positive_int(name: str) -> int:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _get_required_query_param(name, _positive_int, "integer")


def get_optional_non_negative_int(name: str) -> int | None:
    """Parse query for optional parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range or None
    """
    return _get_optional_query_param(name, _non_negative_int, "integer")


def get_optional_positive_int(name: str) -> int | None:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range or None
    """
    return _get_optional_query_param(name, _positive_int, "integer")


def get_optional_str(name: str) -> str | None:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _get_optional_query_param(name)


def parse_non_negative_int(name: str, raw: str) -> int:
    """Parse raw parameter, convert, and validate.

    :param name: Parameter name
    :param raw: Raw parameter value e.g. route parameter
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _parse_param(name, raw, _non_negative_int, "integer")


def _non_empty_str(raw: str, name: str) -> str:
    if not raw:
        raise ValueError
    return raw


def _non_negative_int(raw: str, name: str) -> int:
    value = int(raw)
    if value < 0:
        raise ClientResponseException(
            400, f"Parameter '{name}' must be a non-negative integer"
        )
    return value


def _positive_int(raw: str, name: str) -> int:
    value = int(raw)
    if value <= 0:
        raise ClientResponseException(
            400, f"Parameter '{name}' must be a positive integer"
        )
    return value


def _convert_param(
    name: str,
    raw: str,
    converter: Callable[[str, str], T],
    type_name: str | None,
) -> T:
    try:
        return converter(raw, name)
    except (ValueError, TypeError):
        label = type_name or getattr(converter, "__name__", "value")
        raise ClientResponseException(
            400, f"Parameter '{name}' must be a valid {label} (got: '{raw}')"
        )


def _get_required_query_param(
    name: str,
    converter: Callable[[str, str], T] = _non_empty_str,
    converter_type: str = "string",
) -> T:
    raw = request.args.get(name)
    if raw is None:
        raise ClientResponseException(400, f"Missing required parameter: '{name}'")
    return _convert_param(name, raw, converter, converter_type)


def _get_optional_query_param(
    name: str,
    converter: Callable[[str, str], T] = _non_empty_str,
    converter_type: str = "string",
) -> T | None:
    raw = request.args.get(name)
    if raw is None:
        return None
    return _convert_param(name, raw, converter, converter_type)


def _parse_param(
    name: str,
    raw: str,
    converter: Callable[[str, str], T] = _non_empty_str,
    converter_type: str = "string",
) -> T:
    return _convert_param(name, raw, converter, converter_type)


# - Semantic validation
# - The caller must provide syntactically valid incoming parameters
# - Additional arguments must be "fully" validated


def validate_chrom(
    taxa_id: int, chrom: str, start: int | None, end: int | None
) -> None:
    """Validate chromosome, start and end.

    This function performs "piecemeal" validation,
    allowing start and/or end to be missing; whether
    these are required or not must be validated by
    the caller.

    :param taxa_id: A valid taxon identifier (the
    caller must provide a fully validated value)
    :param chrom: Chromosome (the caller must
    provide a syntactically valid value or None)
    :param start: Chromosome start (the caller must
    provide a syntactically valid value or None)
    :param end: Chromosome end (the caller must
    provide a syntactically valid value or None)
    :raises ClientResponseException: 400, 404
    """
    _get_chroms_and_validate(taxa_id, chrom, start, end)


def validate_project_write_permission(smid: str) -> None:
    """Validate if user is allowed to add datasets to the given project.

    :param smid: Project identifier (SMID)
    :raises ClientResponseException: 403, 404
    """
    permission_service = get_permission_service()
    user = _get_valid_user()
    if not permission_service.may_change_project(user, smid):
        raise ClientResponseException(
            403,
            f"Forbidden to access project '{smid}'",
        )


def validate_dataset_write_permission(dataset: Dataset) -> None:
    """Validate if a user is allowed to modify a dataset.

    :param smid: Dataset
    :raises ClientResponseException: 403, 404
    """
    permission_service = get_permission_service()
    user = _get_valid_user()
    if not permission_service.may_change_dataset(user, dataset):
        raise ClientResponseException(
            403,
            f"Forbidden to access dataset '{dataset.id}'",
        )


def validate_request_size(max_size: int) -> None:
    """Validate request size.

    :param max_size: Maximum size allowed.
    :raises FileTooLargeException: 413
    """
    if request.content_length is not None and request.content_length > max_size:
        raise FileTooLargeException(max_size)


def _get_chroms_and_validate(
    taxa_id: int, chrom: str, start: int | None, end: int | None
) -> dict[str, int]:
    assembly_service = get_assembly_service()
    chrom_size: dict[str, int] = {
        d["chrom"]: d["size"] for d in assembly_service.get_chroms(taxa_id)
    }
    if chrom not in chrom_size:
        raise ClientResponseException(
            404, f"chrom '{chrom}' for taxaId '{taxa_id}' not found"
        )

    start = start if start is not None else 0
    end = end if end is not None else chrom_size[chrom]
    if end <= start:
        raise ClientResponseException(
            400,
            "Parameter 'end'/'chromEnd' must be greater than 'start'/'chromStart'",
        )
    if not end <= chrom_size[chrom]:
        raise ClientResponseException(
            400,
            "Parameter 'end'/'chromEnd' is greater than chrom size",
        )
    return chrom_size


def _validate_rna_type(rna_type: str) -> None:
    utilities_service = get_utilities_service()
    valid_rna_types = [obj["id"] for obj in utilities_service.get_rna_types()]
    if rna_type not in valid_rna_types:
        raise ClientResponseException(
            404,
            f"rnaType '{rna_type}' not found",
            "Use GET /catalogs/rna-types for valid RNA types",
        )


def _validate_taxa_id(taxa_id: int) -> None:
    utilities_service = get_utilities_service()
    valid_taxa_ids = [obj["taxa_id"] for obj in utilities_service.get_taxa()]
    if taxa_id not in valid_taxa_ids:
        raise ClientResponseException(
            404,
            f"taxaId '{taxa_id}' not found",
            "Use GET /catalogs/taxa for valid taxa",
        )


# TODO MS14
# biotypes are independent of species/RNA type
def _validate_biotypes(biotypes: list[str], rna_type: str) -> None:
    utilities_service = get_utilities_service()
    valid_biotypes = utilities_service.get_biotypes()["biotypes"]
    unknown_biotypes = [
        biotype for biotype in biotypes if biotype not in valid_biotypes
    ]
    if unknown_biotypes:
        raise ClientResponseException(
            404,
            f"biotypes '{', '.join(unknown_biotypes)}' not found",
            "Use GET /catalogs/rna-types/<rnaType>/biotypes for valid biotypes",
        )


# TODO MS14
def _validate_features(features: list[str], rna_type: str) -> None:
    annotation_service = get_annotation_service()
    try:
        valid_features = annotation_service.get_features_by_rna_type(rna_type)
    except NotImplementedError as exc:
        raise ClientResponseException(
            501, f"rnaType '{rna_type}' not implemented"
        ) from exc
    unknown_features = [
        feature for feature in features if feature not in valid_features
    ]
    if unknown_features:
        raise ClientResponseException(
            404,
            f"features '{', '.join(unknown_features)}' not found",
            "Use GET /catalogs/rna-types/<rnaType>/features for valid features",
        )


def _validate_selections(selections: list[tuple[int, int, int]]) -> None:
    utilities_service = get_utilities_service()
    valid_selections = [
        (obj["modification_id"], obj["organism_id"], obj["technology_id"])
        for obj in utilities_service.get_selections()
    ]
    unknown_selections = [s for s in selections if s not in valid_selections]
    if unknown_selections:
        raise ClientResponseException(
            404,
            (
                "(modification, organism, technology) "
                f"'{', '.join(map(str, unknown_selections))}' not found."
            ),
            (
                "Use GET /catalogs/selections for valid combinations of "
                "modification, organism, and technology identifiers"
            ),
        )


def _get_valid_user() -> User:
    email = get_jwt_identity()
    user_service = get_user_service()
    try:
        return user_service.get_user_by_email(email)
    except NoSuchUser:
        raise ClientResponseException(404, f"User '{email}' not found")


def _is_valid_identifier(identifier, length):
    if not VALID_DATASET_ID_REGEXP.match(identifier):
        return False
    elif len(identifier) != length:
        return False
    return True


# - Helpers


def get_unique_list_from_query_param(name: str, list_type) -> list[Any]:
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

    Note: the caller should provide an explicit parser for types
    other than Text and Numeric.
    """
    result_as_set = {
        *request.args.getlist(name, type=list_type),
        *request.args.getlist(f"{name}[]", type=list_type),
    }
    return list(result_as_set)


def get_valid_rna_type() -> str:
    """Parse query for RNA type and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated RNA type
    """
    rna_type = _get_required_query_param("rnaType")
    _validate_rna_type(rna_type)
    return rna_type


def parse_valid_rna_type(raw: str) -> int:
    """Parse raw RNA type and validate.

    :param raw: Route parameter for RNA type
    :raises ClientResponseException: 400, 404
    :return: The validated RNA type
    """
    rna_type = _parse_param("rna_type", raw)
    _validate_rna_type(rna_type)
    return rna_type


def get_valid_taxa_id() -> int:
    """Parse query for taxon identifier and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated taxon identifier
    """
    taxa_id = get_positive_int("taxaId")
    _validate_taxa_id(taxa_id)
    return taxa_id


def parse_valid_taxa_id(raw: str) -> int:
    """Parse raw taxon identifier and validate.

    :param raw: Route parameter for taxon identifier
    :raises ClientResponseException: 400, 404
    :return: The validated taxon identifier
    """
    taxa_id = _parse_param("taxa_id", raw, _positive_int, "integer")
    _validate_taxa_id(taxa_id)
    return taxa_id


def get_valid_biotypes() -> list[str]:
    """Parse query for biotypes and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated list of biotypes
    """
    rna_type = get_valid_rna_type()
    biotypes = get_unique_list_from_query_param("biotypes", str)
    _validate_biotypes(biotypes, rna_type)
    return biotypes


def get_valid_features() -> list[str]:
    """Parse query for features and validate.

    :raises ClientResponseException: 400, 404, 501
    :return: The validated list of features
    """
    rna_type = get_valid_rna_type()
    features = get_unique_list_from_query_param("features", str)
    _validate_features(features, rna_type)
    return features


def get_valid_selections() -> tuple[int, int, list[int]]:
    """Parse query for selections and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated modification, organism, and
    technology identifiers
    """
    modification_id = get_non_negative_int("modification")
    organism_id = get_non_negative_int("organism")
    technology_ids = get_unique_list_from_query_param("technology", int)
    if not technology_ids:
        raise ClientResponseException(400, "Missing required parameter: 'technology'")
    technology_ids = [_non_negative_int(tid, "technology") for tid in technology_ids]
    selections = [(modification_id, organism_id, tid) for tid in technology_ids]
    _validate_selections(selections)
    return modification_id, organism_id, technology_ids


def get_valid_coords(
    context: int = 0,
) -> tuple[str, int, int, Strand]:
    """Parse query for coordinates and validate.

    NOTE: This function uses "start" and "end",
    not "chromStart", "chromEnd".

    :param context: Number of bases to include in
    context around start-end.
    :raises ClientResponseException: 400, 404
    :return: Coordinates as (chrom, start, end, strand)
    """
    taxa_id = get_valid_taxa_id()
    chrom = _get_required_query_param("chrom")
    start = get_non_negative_int("start")
    end = get_positive_int("end")
    chrom_size = _get_chroms_and_validate(
        taxa_id,
        chrom,
        start,
        end,
    )

    strand = request.args.get("strand", default=".", type=str)
    try:
        strand_dto = Strand(strand)
    except ValueError as exc:
        raise ClientResponseException(
            400, "Parameter 'strand' must be +, -, or ."
        ) from exc

    if context > 0:
        start = start - context
        start = max(start, 0)
        end = end + context
        end = min(end, chrom_size[chrom])

    return chrom, start, end, strand_dto


def parse_valid_target_type(raw: str) -> TargetsFileType:
    """Parse raw target and return target file type value.

    :param raw: Incoming target type
    :raises ClientResponseException: 400
    :return: The value corresponding to target
    """
    target = _parse_param("target", raw)
    try:
        return TargetsFileType[target]
    except KeyError:
        raise ClientResponseException(
            400,
            f"Parameter 'target' must be: {TargetsFileType.list()}",
        )


def parse_valid_sunburst_type(raw: str) -> SunburstChartType:
    """Parse raw chart type and return chart type value.

    :param raw: Incoming chart type
    :raises ClientResponseException: 400
    :return: The value corresponding to raw chart type
    """
    sunburst_type = _parse_param("sunburstType", raw)
    try:
        return SunburstChartType[sunburst_type]
    except KeyError as exc:
        raise ClientResponseException(
            400,
            f"Parameter 'sunburstType' must be: {SunburstChartType.list()}",
        ) from exc


def get_valid_dataset(raw: str) -> Dataset:
    """Get a valid dataset.

    :param raw: Incoming dataset identifier (EUFID)
    :raises ClientResponseException: 400, 404.
    :return: Dataset
    """
    dataset_id = _parse_param("datasetId", raw)
    if not _is_valid_identifier(dataset_id, Identifiers.EUFID.length):
        raise ClientResponseException(400, f"Invalid datasetId '{dataset_id}'")
    dataset_service = get_dataset_service()
    try:
        return dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        raise ClientResponseException(404, f"Dataset '{dataset_id}' not found")


def get_valid_bam_file(dataset: Dataset, raw: str) -> BamFile:
    """Get BAM file.

    :param dataset: Dataset
    :param raw: File name
    :raises ClientResponseException: 400, 404.
    :return: BAM file object
    """
    name = _parse_param("BamName", raw)
    if not VALID_FILENAME_REGEXP.match(name):
        raise ClientResponseException(400, f"Invalid BamName '{name}'")
    file_service = get_file_service()
    try:
        return file_service.get_bam_file(dataset, name)
    except NoResultFound:
        raise ClientResponseException(
            404,
            f"BAM file '{name}' not found or no association with dataset '{dataset.id}'",
        )


def get_valid_dataset_id_list_from_request_parameter(parameter: str) -> list[str]:
    """Get a list of valid dataset IDs.

    :param parameter: Query parameter
    :raises ClientResponseException: 400, 404.
    :return: List of dataset ID(s)
    """
    as_list = get_unique_list_from_query_param(parameter, str)
    if len(as_list) > MAX_DATASET_IDS_IN_LIST:
        raise ClientResponseException(
            400,
            f"'{parameter}' contains too many datasetId (max. {MAX_DATASET_IDS_IN_LIST})",
        )
    dataset_service = get_dataset_service()
    for dataset_id in as_list:
        if not _is_valid_identifier(dataset_id, Identifiers.EUFID.length):
            raise ClientResponseException(
                400, f"Invalid {parameter} datasetId '{dataset_id}'"
            )
        try:
            dataset_service.get_by_id(dataset_id)
        except NoResultFound as exc:
            raise ClientResponseException(
                404, f"{parameter} datasetId '{dataset_id}' not found"
            ) from exc
    return as_list


def get_valid_tmp_file_id_from_request_parameter(
    parameter: str, is_optional=False
) -> Optional[str]:
    """Get uploaded/temporary file identifier.

    :param parameter: Query parameter
    :param is_optional: True if parameter is required (Default: False)
    :raises ClientResponseException: 400, 404
    :return: Uploaded/temporary file identifier or None
    """
    file_id = request.args.get(parameter, type=str)
    if not file_id:
        if is_optional:
            return None
        raise ClientResponseException(400, f"Missing required parameter: '{parameter}'")
    if not VALID_FILENAME_REGEXP.match(file_id):
        raise ClientResponseException(400, f"Invalid {parameter} fileId '{file_id}'")
    file_service = get_file_service()
    if not file_service.check_tmp_upload_file_id(file_id):
        raise ClientResponseException(
            404,
            f"{parameter} file not found",
            "Select the file again and try to re-upload",
        )
    return file_id


def get_valid_remote_file_name_from_request_parameter(
    parameter: str, default: str = "uploaded file"
) -> str:
    """Get uploaded/temporary file name.

    :param parameter: Query parameter
    :type parameter: str
    :param default: Default file name
    :type default: str
    :return: Uploaded/temporary file name
    """
    file_name = request.args.get(parameter, type=str)
    if not file_name:
        return default
    return re.sub(INVALID_CHARS_REGEXP, "?", file_name)


def get_valid_boolean_from_request_parameter(
    parameter: str, default: Optional[bool] = None
) -> bool:
    """Parse query parameter to boolean value.

    :param parameter: Query parameter
    :param default: Default value. If query
    parameter is None, and there is no default,
    a ClientResponseException is raised.
    :raises ClientResponseException: 400
    :return: Boolean value
    """
    raw_value = request.args.get(parameter, type=str)
    if raw_value is None:
        if default is None:
            raise ClientResponseException(
                400, f"Missing required parameter: '{parameter}' ('true' or 'false')"
            )
        return default
    lower_case_value = raw_value.lower()
    if lower_case_value == "false":
        return False
    if lower_case_value == "true":
        return True
    raise ClientResponseException(
        400, f"Invalid value for '{parameter}' (allowed: 'true', 'false')"
    )


# Response


def get_response_from_pydantic_object(obj: BaseModel):
    return Response(
        response=obj.model_dump_json(), status=200, mimetype="application/json"
    )
