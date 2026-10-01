"""Provide syntactically valid data out of the HTTP request.

- Query parameter parsing/conversion
- Route parameter parsing/conversion
- JSON body parsing/structural validation
- Request size validation
"""

import re
from typing import Any, TypeVar
from collections.abc import Callable

from flask import request

from scimodom.utils.specs.enums import (
    TargetsFileType,
    SunburstChartType,
)

from .errors import (
    ClientResponseException,
    FileTooLargeException,
    _invalid_choice,
)


T = TypeVar("T")

_FILENAME_CHARS = r"a-zA-Z0-9.,_-"
VALID_FILENAME_REGEXP = re.compile(rf"\A[{_FILENAME_CHARS}]{{1,256}}\Z")
INVALID_CHARS_REGEXP = re.compile(rf"[^{_FILENAME_CHARS}]")
VALID_DATASET_ID_REGEXP = re.compile(r"\A[a-zA-Z0-9]{1,256}\Z")


# Query parameter parsing/conversion


def get_non_negative_int(name: str) -> int:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _get_required_query_param(name, _non_negative_int)


def get_optional_non_negative_int(name: str) -> int | None:
    """Parse query for optional parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range or None
    """
    return _get_optional_query_param(name, _non_negative_int)


def get_positive_int(name: str) -> int:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range
    """
    return _get_required_query_param(name, _positive_int)


def get_optional_positive_int(name: str) -> int | None:
    """Parse query for parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The converted value in the given range or None
    """
    return _get_optional_query_param(name, _positive_int)


def get_optional_str(name: str) -> str | None:
    """Parse query for parameter, validate (not empty).

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: The non-empty string or None
    """
    return _get_optional_query_param(name)


def get_optional_bool(name: str) -> bool | None:
    """Parse query parameter, convert, and validate.

    :param name: Query parameter name
    :raises ClientResponseException: 400
    :return: Boolean corresponding to the parameter value, or None
    """
    return _get_optional_query_param(name, _bool)


def get_required_list(name: str, list_type: type[T]) -> list[T]:
    """Parse query parameters (at least one value is required).

    :param name: Query parameter name
    :param list_type: Element type
    :raises ClientResponseException: 400
    :return: The non-empty list of converted values
    """
    values = _get_list_query_param(name, list_type)
    if not values:
        raise ClientResponseException(
            400,
            f"Missing required parameter: '{name}'",
        )
    return values


def get_optional_list(name: str, list_type: type[T]) -> list[T]:
    """Parse query parameters.

    NOTE: returns [] if absent or empty

    :param name: Query parameter name
    :param list_type: Element type
    :raises ClientResponseException: 400
    :return: The list of converted values, possibly empty
    """
    return _get_list_query_param(name, list_type)


def get_valid_target_type() -> TargetsFileType:
    """Parse query for target and return target file type value.

    :raises ClientResponseException: 400
    :return: The value corresponding to target
    """
    return _parse_enum_member(
        "target",
        request.args.get("target"),
        TargetsFileType,
    )


def get_valid_file_name(name: str, default: str = "upload") -> str:
    """Get a valid file name, e.g. for tmp uploads.

    NOTE: Return a safe, clean, possibly
    truncated, file name

    :param name: Query parameter name
    :param default: Default file name
    :return: Clean file name
    """
    file_name = request.args.get(name, type=str)
    if not file_name:
        return default
    return re.sub(INVALID_CHARS_REGEXP, "?", file_name)[:256]


# Route parameter parsing/conversion


def validate_file_name(name: str, raw: str) -> str:
    """Parse and validate a file name.

    NOTE: Contrary to `get_valid_file_name`,
    raise an exception for invalid characters

    :param name: Route parameter name
    :param raw: Route parameter value
    :raises ClientResponseException: 400
    :return: Parsed name
    """
    _validate_file_name(name, _parse_param(name, raw))


def parse_valid_sunburst_type(raw: str) -> SunburstChartType:
    """Parse raw chart type and return chart type value.

    :param raw: Route parameter for chart type
    :raises ClientResponseException: 400
    :return: The value corresponding to raw chart type
    """
    return _parse_enum_member(
        "sunburstType",
        _parse_param("sunburstType", raw),
        SunburstChartType,
    )


# JSON body parsing/structural validation


def get_required_json_fields(*fields: str) -> dict[str, Any]:
    """Validate JSON object, i.e. if it contains given fields.

    NOTE: Does not perform field validation

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


# Request size validation


def validate_request_size(max_size: int) -> None:
    """Validate request size.

    :param max_size: Maximum size allowed.
    :raises FileTooLargeException: 413
    """
    if request.content_length is not None and request.content_length > max_size:
        raise FileTooLargeException(max_size)


# Private (for all helpers)


_BOOLEANS = {
    "true": True,
    "false": False,
}


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


def _bool(raw: str, name: str) -> bool:
    try:
        return _BOOLEANS[raw.lower()]
    except KeyError:
        _invalid_choice(name, raw, ", ".join(f"'{b}'" for b in _BOOLEANS))


def _convert_param(
    name: str,
    raw: str,
    converter: Callable[[str, str], T],
) -> T:
    # propagates ClientResponseException
    try:
        return converter(raw, name)
    except (ValueError, TypeError):
        label = getattr(converter, "__name__", "value")
        raise ClientResponseException(
            400, f"Parameter '{name}' must be a valid {label} (got: '{raw}')"
        )


def _get_required_query_param(
    name: str,
    converter: Callable[[str, str], T] = _non_empty_str,
) -> T:
    raw = request.args.get(name)
    if raw is None:
        raise ClientResponseException(400, f"Missing required parameter: '{name}'")
    return _convert_param(name, raw, converter)


def _get_optional_query_param(
    name: str,
    converter: Callable[[str, str], T] = _non_empty_str,
) -> T | None:
    raw = request.args.get(name)
    if raw is None:
        return None
    return _convert_param(name, raw, converter)


def _get_list_query_param(name: str, list_type: type[T]) -> list[T]:
    # returns an empty list if parameter is absent
    # empty elements are not silently skipped!
    is_str = list_type is str
    label = "non-empty str" if is_str else getattr(list_type, "__name__", "value")
    result: list[T] = []
    for raw in request.args.getlist(name):
        try:
            if is_str and not raw:
                raise ValueError
            result.append(list_type(raw))
        except (ValueError, TypeError) as exc:
            raise ClientResponseException(
                400,
                f"Parameter '{name}' must be a valid {label} (got: '{raw}')",
            ) from exc
    return result


def _parse_param(
    name: str,
    raw: str,
    converter: Callable[[str, str], T] = _non_empty_str,
) -> T:
    return _convert_param(name, raw, converter)


def _parse_enum_member(name: str, raw: str, enum_cls: type[T]) -> T:
    try:
        return enum_cls[raw]
    except KeyError:
        _invalid_choice(name, raw, enum_cls.list())


def _is_valid_identifier(identifier: str, length: int) -> bool:
    return bool(VALID_DATASET_ID_REGEXP.match(identifier) and len(identifier) == length)


def _validate_file_name(name: str, raw: str) -> None:
    if not VALID_FILENAME_REGEXP.match(raw):
        raise ClientResponseException(400, f"Invalid {name} file name: '{raw}'")
