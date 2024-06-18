import inspect
import re
import uuid
from collections.abc import Sequence, Iterable
from itertools import chain
from typing import Any

import requests  # type: ignore
import shortuuid

import scimodom.database.models as models


# various helper functions
# NOTE: location of these may change


def check_keys_exist(d: Iterable[Any], keys: Iterable[Any]) -> list[Any]:
    """Check if keys are present in the dictionary, w/o
    type, value, etc. validation.

    Note: Returned value unused.

    :param d: An iterable e.g. keys from a dictionary
    :type d: Iterable
    :param keys: An iterable, e.g. keys to check.
    :type keys: Iterable
    :returns: missing_keys
    :rtype: list
    """

    missing_keys = [k for k in keys if k not in d]

    if len(missing_keys) > 0:
        msg = " ".join(missing_keys)
        msg = f"Keys not found: {msg}."
        raise KeyError(msg)

    return missing_keys


def get_model(model: str):
    """Get model class by name.

    :param model: Name of class
    :type model: str
    :returns: The model class
    :rtype: Base
    """

    try:
        return {
            name: cls
            for name, cls in inspect.getmembers(models, inspect.isclass)
            if cls.__module__ == models.__name__
        }[model]
    except Exception:
        msg = f"Model undefined: {model}."
        raise KeyError(msg)


def get_table_columns(model, remove: list[str] | None = None) -> list[str]:
    """Get columns from model table, optionally
    removing a subset of them.

    :param model: Name of class or SQLAlchemy model
    :type model: Base | str
    :param remove: List of column names
    :type remove: list
    :returns: List of columns
    :rtype: list
    """
    if remove is None:
        remove = []
    try:
        cols = model.__table__.columns
    except Exception:
        cols = get_model(model).__table__.columns
    return [c.key for c in cols if c.key not in remove]


def get_table_column_python_types(model, remove: list[str] | None = None) -> list[Any]:
    """Get column python types from model table, optionally
    removing a subset of them.

    Note: Python types str, int, bool

    :param model: Name of class or SQLAlchemy model
    :type model: Base | str
    :param remove: List of column names
    :type remove: str
    :returns: List of column (Python) types
    :rtype: list
    """

    if remove is None:
        remove = []
    try:
        cols = model.__table__.columns
    except Exception:
        cols = get_model(model).__table__.columns
    return [c.type.python_type for c in cols if c.key not in remove]


def to_list(i: int | float | str | list | set | None):
    """Converts numerical, string, list, set, and None to list,
    but does not unpack tuple or dict.

    :param i: String, list, set, or None
    :type i: str | list | set | None
    :returns: Input as a list
    :rtype: list
    """
    return (
        i
        if isinstance(i, list)
        else list(i)
        if isinstance(i, set)
        else []
        if i is None
        else [i]
    )


def flatten_list(items: list | Sequence | Iterable) -> list:
    """Flatten list.

    :param items: list
    :type items: list
    :returns: flattened list
    :rtype: list
    """

    return list(chain.from_iterable(items))


def gen_short_uuid(length: int, suuids: Sequence[Any]) -> str:
    """Generate a short UUID.

    :param length: Length of ID
    :type length: int
    :param suuids: List of existing IDs
    :type suuids: list
    :returns: Newly created ID
    :rtype: str
    """

    u = uuid.uuid4()
    suuid = shortuuid.encode(u)[:length]
    while suuid in suuids:
        suuid = shortuuid.encode(u)[:length]
    return suuid


R_SEMICOLON = re.compile(r"\s*;\s*")
R_COMMA = re.compile(r"\s*,\s*")
R_KEYVALUE = re.compile(r"(\s+|\s*=\s*)")


def _get_gtf_value(value: str | None) -> str | None:
    """Parse GTF attribute value

    :param value: GTF attribute value
    :type value: str | None
    :returns: Clean value or None
    :rtype: str | None
    """
    if not value:
        return None
    value = value.strip("\"'")
    if value in ["", ".", "NA"]:
        return None

    return value


def parse_gtf_attributes(attrs_str: str) -> dict[str | Any, str | None]:
    """Parse GTF attributes

    :param attrs_str: GTF attributes (from pybedtools interval fields)
    :type attrs_str: str
    :returns: Dictionary of attributes
    :rtype: dict
    """
    attrs = [x for x in re.split(R_SEMICOLON, attrs_str) if x.strip()]
    result = dict()

    for attr in attrs:
        try:
            key, _, value = re.split(R_KEYVALUE, attr, 1)
        except ValueError:
            continue
        result[key] = _get_gtf_value(value)

    return result


def get_ensembl_prefix(gene_id: str) -> str:
    """Extract Ensembl prefix for gene identifier.

    :param gene_id: Gene identifier
    :type gene_id: str
    :returns: Prefix
    :rtype: str
    """
    tmp = gene_id[:7]
    if tmp[-1].isdigit():
        return tmp[:3]
    else:
        return tmp[:6]
