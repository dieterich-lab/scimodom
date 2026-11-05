import os
from pathlib import Path

import pytest

from scimodom.config import set_config_from_environment, get_config, set_config

DATA_DIR = Path(__file__).parents[1]

EXPECTED_CONFIG = {
    "DATABASE_URI": "mysql+mysqldb://scimodom:sSCPInTsFzaPNLiSvXAmFZOGPtOwetjk@127.0.0.1:3305/scimodom",
    "SECRET_KEY": "QznPEcsVmKlwixitPAgLYcnLTkSHhXYI",
    "JWT_SECRET_KEY": "QznPEcsVmKlwixitPAgLYcnLTkSHhXYI",
    "SESSION_COOKIE_SECURE": True,
    "SESSION_COOKIE_SAMESITE": "None",
    "SMTP_SERVER": "mail.relay-server.de",
    "SMTP_FROM_ADDRESS": "from@address.org",
    "NOTIFICATION_ADDRESS": "maintainer@institution.de",
    "HTTP_PUBLIC_URL": "http://localhost:5173/",
    "IMPORT_PATH": "import",
    "DATA_PATH": "data",
    "UPLOAD_PATH": "uploads",
    "BEDTOOLS_TMP_PATH": "/tmp/bedtools",
}


def test_config_unset():
    set_config(new_config=None)
    with pytest.raises(Exception) as exc:
        get_config()
    assert (
        str(exc.value) == "Internal error: get_config() called before initialisation!"
    )


@pytest.mark.datafiles(Path(DATA_DIR, ".env.tests.0"))
def test_config(datafiles, mocker):
    mocker.patch.dict(os.environ, clear=True)
    os.environ["ENV_FILE"] = Path(datafiles, ".env.tests.0").as_posix()
    set_config(new_config=None)
    set_config_from_environment()
    config = get_config().__dict__
    for key, expected_value in EXPECTED_CONFIG.items():
        assert config[key] == expected_value


# assert stderr using capsys
# cf. https://github.com/pytest-dev/pytest/issues/5997
@pytest.mark.datafiles(Path(DATA_DIR, ".env.tests.1"))
def test_config_missing_variable(datafiles, mocker):
    mocker.patch.dict(os.environ, clear=True)
    os.environ["ENV_FILE"] = Path(datafiles, ".env.tests.1").as_posix()
    set_config(new_config=None)
    with pytest.raises(SystemExit):
        set_config_from_environment()


@pytest.mark.datafiles(Path(DATA_DIR, ".env.tests.0"))
@pytest.mark.parametrize("debug", [False, True])
def test_config_audit_log_file(datafiles, mocker, tmp_path, debug):
    mocker.patch.dict(os.environ, clear=True)
    os.environ["ENV_FILE"] = Path(datafiles, ".env.tests.0").as_posix()
    os.environ["FLASK_DEBUG"] = str(debug)
    set_config(new_config=None)
    set_config_from_environment()
    default = get_config().LOGGING
    assert "audit_file" not in default["handlers"]
    assert default["loggers"]["scimodom.audit"]["handlers"] == ["audit"]

    audit_file = tmp_path / "audit.log"
    os.environ["AUDIT_LOG_FILE"] = audit_file.as_posix()
    set_config_from_environment()
    config = get_config().LOGGING
    handler = config["handlers"]["audit_file"]
    assert handler["filename"] == audit_file.as_posix()
    assert handler["class"] == "scimodom.cli.helpers.audit.AuditFileHandler"
    assert handler["delay"] is True  # opened at the first record, not at start-up
    assert handler["formatter"] == "audit"
    assert config["loggers"]["scimodom.audit"]["handlers"] == ["audit", "audit_file"]
    # nothing else changes: the audit file is the only difference
    for key in ("root", "formatters"):
        assert config[key] == default[key]
    assert config["handlers"]["default"] == default["handlers"]["default"]
    assert config["handlers"]["audit"] == default["handlers"]["audit"]
    assert set(config["handlers"]) == set(default["handlers"]) | {"audit_file"}
    assert config["loggers"].keys() == default["loggers"].keys()
    # the class level default is not modified (no leak between calls)
    from scimodom.config import Config

    assert "audit_file" not in Config.LOGGING["handlers"]
    assert Config.LOGGING["loggers"]["scimodom.audit"]["handlers"] == ["audit"]
    assert not audit_file.exists()
