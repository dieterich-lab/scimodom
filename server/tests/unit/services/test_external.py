import sys
from subprocess import DEVNULL

import pytest

from scimodom.services.external import ExternalService
from scimodom.utils.specs.enums import IndexCacheType


@pytest.mark.parametrize(
    "cache,command",
    [
        (None, "update"),
        (IndexCacheType.SUNBURST, "update-sunburst"),
        (IndexCacheType.AGGREGATES, "update-aggregates"),
    ],
)
def test_trigger_cache_update(mocker, cache, command):
    popen = mocker.patch("scimodom.services.external.Popen")
    thread = mocker.patch("scimodom.services.external.Thread")
    ExternalService.trigger_cache_update(cache)
    popen.assert_called_once_with(
        [
            sys.executable,  # not 'flask' from PATH
            "-m",
            "flask",
            "--app",
            "scimodom.app",
            "cache",
            command,
        ],
        stdin=DEVNULL,
        start_new_session=True,  # detached from the caller
    )
    # the finished process is reaped (no zombie in a long-running server)
    thread.assert_called_once_with(target=popen.return_value.wait, daemon=True)
    thread.return_value.start.assert_called_once()


def test_trigger_cache_update_propagates_start_failure(mocker):
    mocker.patch("scimodom.services.external.Popen", side_effect=OSError("nope"))
    thread = mocker.patch("scimodom.services.external.Thread")
    with pytest.raises(OSError):
        ExternalService.trigger_cache_update()
    thread.assert_not_called()
