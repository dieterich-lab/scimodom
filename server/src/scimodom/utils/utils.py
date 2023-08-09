
import sys
import logging
logger = logging.getLogger(__name__)

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

    logging_levels = ['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    logging_options = parser.add_argument_group("Logging")

    logging_options.add_argument('--log-file', help="Log file.", default=logf)
    logging_options.add_argument('--log-stdout', help="""Log to stdout in addition
                                 to LOG_FILE if [--log-file LOG_FILE] is given.""", 
                                 action='store_true')
    
    logging_options.add_argument('--logging-level', help="Logging level for all logs", 
                                 choices=logging_levels, default="WARNING")
    logging_options.add_argument('--file-logging-level', help="""Logging level for the
                                 log file if [--log-file]. Overrides [--logging-level]""",
                                 choices=logging_levels, default="NOTSET")


def update_logging(args, 
                   logger=None, 
                   format_str='%(levelname)-8s %(name)-8s %(asctime)s : %(message)s'):
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

    # get root logger
    if logger is None:
        logger = logging.getLogger('')
            
    logger.handlers = []

    # set base logging level
    level = logging.getLevelName(args.logging_level)
    logger.setLevel(level)

    # check additional loggers
    if len(args.log_file) > 0:
        h = logging.FileHandler(args.log_file)
        formatter = logging.Formatter(format_str)
        h.setFormatter(formatter)
        if args.file_logging_level != 'NOTSET':
            l = logging.getLevelName(args.file_logging_level)
            h.setLevel(l)
        logger.addHandler(h)

    if args.log_stdout:
        h = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(format_str)
        h.setFormatter(formatter)
        logger.addHandler(h)

