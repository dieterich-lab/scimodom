# logging_utils


def add_log_opts(parser, logf=""):
    """
    Add options for logging.
    Statements are always written to stderr.

    Parameters
    ----------
    parser
        argparse.ArgumentParser
    logf
        Log file

    Returns
    -------
    None
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
    args, logger=None, format_str="%(levelname)-8s %(name)-8s %(asctime)s : %(message)s"
):
    """
    Configure loggers/handlers.

    Parameters
    ----------
    args
        argparse.Namespace

    logger
        logging.Logger or None. If None, default logger is updated.

    format_str
        Logging format string.

    Returns
    -------
    None
    """
    import sys
    import logging

    # get root logger
    if logger is None:
        logger = logging.getLogger("")

    logger.handlers = []

    # set base logging level
    level = logging.getLevelName(args.logging_level)
    logger.setLevel(level)

    # check additional loggers
    if len(args.log_file) > 0:
        h = logging.FileHandler(args.log_file)
        formatter = logging.Formatter(format_str)
        h.setFormatter(formatter)
        if args.file_logging_level != "NOTSET":
            l = logging.getLevelName(args.file_logging_level)
            h.setLevel(l)
        logger.addHandler(h)

    if args.log_stdout:
        h = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(format_str)
        h.setFormatter(formatter)
        logger.addHandler(h)


# various helper functions
# NOTE: location of these may change, e.g. to service.utils


def check_keys_exist(d, keys):
    """
    Check if keys are present in the dictionary, w/o
    type, value, etc. validation.

    Parameters
    ----------
    d (dict)
        A dictionary.
    keys (list)
        A list of keys to check.

    Returns
    -------
    list of keys that are not found

    Raises
    ------
    KeyError
    """

    missing_keys = [k for k in keys if k not in d]

    if len(missing_keys) > 0:
        missing_keys = " ".join(missing_keys)
        msg = f"Keys not found: {missing_keys}."
        raise KeyError(msg)

    return missing_keys


def get_model(model):
    """
    Get model class by name.

    Parameters
    ----------
    model
        Name of class.

    Returns
    -------
    Class
        The model class.
    """

    import inspect
    import scimodom.database.models as models

    try:
        return {
            name: cls
            for name, cls in inspect.getmembers(models, inspect.isclass)
            if cls.__module__ == models.__name__
        }[model]
    except:
        msg = f"Model undefined: {model}."
        raise KeyError(msg)


def get_table_columns(model, remove=[]):
    """
    Get columns from model table, optionally
    removing a subset of them.

    Parameters
    ----------
    model
        Name of class.
    remove
        List of column names

    Returns
    -------
    List of columns.
    """

    try:
        cols = model.__table__.columns
    except:
        cols = get_model(model).__table__.columns
    return [c.key for c in cols if c.key not in remove]


def get_table_column_python_types(model, remove=[]):
    """
    Get column python types from model table, optionally
    removing a subset of them.

    Parameters
    ----------
    model
        Name of class.
    remove
        List of column names

    Returns
    -------
    List of column python types.
    """

    try:
        cols = model.__table__.columns
    except:
        cols = get_model(model).__table__.columns
    return [c.type.python_type for c in cols if c.key not in remove]


def to_list(i):
    # converts string, list, set, and None to list
    # does not unpack tuple or dict
    return (
        i
        if isinstance(i, list)
        else list(i)
        if isinstance(i, set)
        else []
        if i is None
        else [i]
    )


def gen_short_uuid(LENGTH, suuids):
    import uuid
    import shortuuid

    u = uuid.uuid4()
    suuid = shortuuid.encode(u)[:LENGTH]
    while suuid in suuids:
        suuid = shortuuid.encode(u)[:LENGTH]
    return suuid
