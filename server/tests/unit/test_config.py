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
