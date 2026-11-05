import logging

import pytest

from scimodom.cli.helpers.audit import AUDIT_LOGGER_NAME


@pytest.fixture(autouse=True)
def isolate_audit_logger():
    """Do not forward the audit records to the root logger.

    With pytest's live logging (log_cli), a record emitted while Click's
    CliRunner has replaced stdout makes the runner fail with 'I/O
    operation on closed file'. Tests of the audit trail attach their own
    handler to the audit logger.
    """
    logger = logging.getLogger(AUDIT_LOGGER_NAME)
    propagate = logger.propagate
    logger.propagate = False
    yield
    logger.propagate = propagate
