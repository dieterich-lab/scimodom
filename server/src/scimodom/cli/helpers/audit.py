"""Audit trail for state-changing CLI commands."""

import json
import logging
import os
import pwd
import sys
import time
from functools import wraps
from logging.handlers import WatchedFileHandler

import click

AUDIT_LOGGER_NAME = "scimodom.audit"

audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)


class UtcFormatter(logging.Formatter):
    """Format the time of the records in UTC."""

    converter = time.gmtime


class AuditFileHandler(WatchedFileHandler):
    """Write to a file, reopened if rotated, without ever raising.

    A failure to write is reported on stderr; raised by emit or
    passed to handleError.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record.

        :param record: logging record
        """
        try:
            super().emit(record)
        except Exception as exc:  # noqa
            self._warn(exc)

    def handleError(self, record: logging.LogRecord) -> None:
        """Handle errors which occur during an emit() call.

        :param record: logging record
        """
        self._warn(sys.exc_info()[1])

    def _warn(self, exc: BaseException | None) -> None:
        print(
            f"Warning: failed to log audit record to '{self.baseFilename}': {exc}",
            file=sys.stderr,
        )


def _get_os_user() -> str:
    uid = os.getuid()
    try:
        # not USER/LOGNAME: these are set by the caller
        return f"{pwd.getpwuid(uid).pw_name}"
    except KeyError:  # e.g. arbitrary uid in a container
        return f"uid: {uid}"


def _format(action: str, state: str, **fields) -> str:
    parts = {"event": action, "state": state, **fields}
    return " ".join(f"{key}={value}" for key, value in parts.items())


def audited(action: str):
    """Record audit trail to log.

    NOTE: Use below `@register_cli_errors`, so that the original
    exceptions are seen.

    :param action: CLI call action name
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            ctx = click.get_current_context()
            context = {
                "user": _get_os_user(),
                "uid": os.getuid(),
                "command": json.dumps(ctx.command_path),
                "params": json.dumps(ctx.params, default=str, sort_keys=True),
            }
            audit_logger.info(_format(action, "started", **context))

            def finished(outcome: str, **extra):
                audit_logger.info(
                    _format(action, "finished", outcome=outcome, **context, **extra)
                )

            try:
                result = func(*args, **kwargs)
            except (
                click.exceptions.Exit
            ) as exc:  # if we ever call ctx.exit() after parsing
                if exc.exit_code == 0:
                    finished("success")
                else:
                    finished("aborted", exit_code=exc.exit_code)
                raise
            except click.Abort:
                finished("aborted")
                raise
            except KeyboardInterrupt:
                finished("interrupted")
                raise
            except Exception as exc:
                finished("failed", error=json.dumps(f"{type(exc).__name__}: {exc}"))
                raise
            finished("success")
            return result

        return wrapper

    return decorator
