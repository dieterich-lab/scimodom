import os

import pytest

from scimodom.config import set_config_from_environment, get_config


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
    with pytest.raises(Exception) as exc:
        get_config()
    assert (
        str(exc.value) == "Internal error: get_config() called before initialisation!"
    )


# assert stderr using capsys
# cf. https://github.com/pytest-dev/pytest/issues/5997
def test_config_missing_variable(mocker):
    mocker.patch.dict(os.environ, clear=True)
    os.environ["ENV_FILE"] = "tests/.env.tests"
    with pytest.raises(SystemExit) as exc:
        set_config_from_environment()


def test_config(mocker, capsys):
    mocker.patch.dict(os.environ, clear=True)
    os.environ["ENV_FILE"] = "tests/.env.tests"
    # this is missing from the test config
    os.environ["NOTIFICATION_ADDRESS"] = "maintainer@institution.de"
    set_config_from_environment()
    config = get_config().__dict__
    for value, (key, expected_value) in zip(config, EXPECTED_CONFIG.items()):
        assert config[key] == expected_value
