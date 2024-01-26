"""utils
"""

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence, Iterable
import inspect
from itertools import chain
import logging
import re
import sys
from typing import Any
import uuid

import shortuuid

import scimodom.database.models as models

# logging_utils


def add_log_opts(parser: ArgumentParser, logf: str = "") -> None:
    """Add options for logging.

    Note: Statements are always written to stderr.

    :param parser: Argument parser
    :type parser: argparse.ArgumentParser
    :param logf: Log file
    :type logf: str
    """
    logging_levels = ["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    logging_options = parser.add_argument_group("logging options")

    logging_options.add_argument("--log-file", help="Log file.", default=logf)
    logging_options.add_argument(
        "--log-stdout",
        help="""Log to stdout in addition
                                 to LOG_FILE if [--log-file LOG_FILE] is given.""",
        action="store_true",
    )

    logging_options.add_argument(
        "--logging-level",
        help="Logging level for all logs",
        choices=logging_levels,
        default="WARNING",
    )
    logging_options.add_argument(
        "--file-logging-level",
        help="""Logging level for the
                                 log file if [--log-file]. Overrides [--logging-level]""",
        choices=logging_levels,
        default="NOTSET",
    )


def update_logging(
    args: Namespace,
    logger: logging.Logger | None = None,
    format_str: str = "%(levelname)-8s %(name)-8s %(asctime)s : %(message)s",
) -> None:
    """Configure loggers/handlers.

    :param args: Argument Namespace object
    :type args: argparse.Namespace
    :param logger: Logger
    :type logger: logging.Logger | None
    :param format_str: Format string
    :type format_str: str
    """

    # get root logger
    if logger is None:
        logger = logging.getLogger("")

    logger.handlers = []

    # set base logging level
    level = logging.getLevelName(args.logging_level)
    logger.setLevel(level)

    # check additional loggers
    if len(args.log_file) > 0:
        fh = logging.FileHandler(args.log_file)
        formatter = logging.Formatter(format_str)
        fh.setFormatter(formatter)
        if args.file_logging_level != "NOTSET":
            l = logging.getLevelName(args.file_logging_level)
            fh.setLevel(l)
        logger.addHandler(fh)

    if args.log_stdout:
        sh = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(format_str)
        sh.setFormatter(formatter)
        logger.addHandler(sh)


# various helper functions
# NOTE: location of these may change, e.g. to service.utils


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
    except:
        msg = f"Model undefined: {model}."
        raise KeyError(msg)


def get_table_columns(model, remove: list[str] = []) -> list[str]:
    """Get columns from model table, optionally
    removing a subset of them.

    :param model: Name of class or SQLAlchemy model
    :type model: Base | str
    :param remove: List of column names
    :type remove: list
    :returns: List of columns
    :rtype: list
    """

    try:
        cols = model.__table__.columns
    except:
        cols = get_model(model).__table__.columns
    return [c.key for c in cols if c.key not in remove]


def get_table_column_python_types(model, remove: list[str] = []) -> list[Any]:
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

    try:
        cols = model.__table__.columns
    except:
        cols = get_model(model).__table__.columns
    return [c.type.python_type for c in cols if c.key not in remove]


def to_list(i: str | list | set | None):
    """Converts string, list, set, and None to list,
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


def flatten_list(l: list | Sequence | Iterable) -> list:
    """Flatten list.

    :param l: list
    :type l: list
    :returns: flattened list
    :rtype: list
    """

    return list(chain.from_iterable(l))


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


# script-related utilities


def confirm(msg: str) -> bool:
    """Prompt confirmation (case-insensitive).

    :param msg: Prompt message
    :type msg: str
    :returns: True if the answer is Y/y
    :rtype: bool
    """

    answer = ""
    while answer not in ["y", "n"]:
        prompt = f"{msg}\nConfirm to continue [Y/N]? "
        answer = input(prompt).lower()
    return answer == "y"
