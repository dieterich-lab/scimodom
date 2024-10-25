import datetime
import logging
import os
from copy import deepcopy
from pathlib import Path
from sys import stderr
from typing import ClassVar

from dotenv import load_dotenv

DEFAULT_FRONTEND_PATH = (
    Path(__file__).parent.parent.parent.parent.joinpath("client").joinpath("dist")
)


class Config:
    """Set Flask and logging variables.

    :param import_dir: Import directory (package)
    :type import_dir: Path | str
    """

    ENV_FILE: ClassVar[str] = ""
    DATABASE_URI: ClassVar[str] = ""
    SECRET_KEY: ClassVar[str] = ""
    SMTP_SERVER: ClassVar[str] = ""
    SMTP_FROM_ADDRESS: ClassVar[str] = ""
    NOTIFICATION_ADDRESS: ClassVar[str] = ""
    HTTP_PUBLIC_URL: ClassVar[str] = ""
    FLASK_DEBUG: ClassVar[bool] = False
    SESSION_COOKIE_SAMESITE: ClassVar[str | None] = None
    SESSION_COOKIE_SECURE: ClassVar[bool] = True
    JWT_SECRET_KEY: ClassVar[str | None] = ""
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)
    IMPORT_PATH: ClassVar[str | Path] = "import"
    DATA_PATH: ClassVar[str | Path] = "data"
    UPLOAD_PATH: ClassVar[str | Path] = "uploads"
    FRONTEND_PATH: ClassVar[Path] = Path(DEFAULT_FRONTEND_PATH)
    BEDTOOLS_TMP_PATH: ClassVar[str | Path] = "/tmp/bedtools"
    LOGGING = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        handlers={
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": logging.WARNING,
            }
        },
        root={
            "handlers": ["default"],
            "level": logging.WARNING,
        },
    )


_config: Config | None = None


def get_config() -> Config:
    if _config is None:
        raise Exception("Internal error: get_config() called before initialisation!")
    return _config


def set_config(new_config: Config | None):
    global _config
    _config = new_config


def set_config_from_environment():
    env_file = os.getenv("ENV_FILE", ".env")
    load_dotenv(env_file)

    def get_required_parameter(name: str):
        try:
            return os.environ[name]
        except KeyError:
            print(
                f"Required parameter '{name}' not set. Please check the file '{env_file}'.",
                file=stderr,
            )
            exit(1)

    def get_logging(debug):
        result = deepcopy(Config.LOGGING)
        if debug:
            result["formatters"]["default"][
                "format"
            ] = "%(asctime)s:%(msecs)03d [%(levelname)s] %(name)s.%(funcName)s.%(lineno)d | %(message)s"
            result["handlers"]["default"]["level"] = logging.DEBUG
            result["root"]["level"] = logging.DEBUG
        return result

    class _Config(Config):
        """Set Flask and logging variables.

        :param import_dir: Import directory (package)
        :type import_dir: Path | str
        """

        ENV_FILE = env_file
        DATABASE_URI = get_required_parameter("DATABASE_URI")
        SECRET_KEY = get_required_parameter("SECRET_KEY")
        SMTP_SERVER = get_required_parameter("SMTP_SERVER")
        SMTP_FROM_ADDRESS = get_required_parameter("SMTP_FROM_ADDRESS")
        NOTIFICATION_ADDRESS = get_required_parameter("NOTIFICATION_ADDRESS")
        HTTP_PUBLIC_URL = get_required_parameter("HTTP_PUBLIC_URL")

        FLASK_DEBUG = eval(os.getenv("FLASK_DEBUG", str(Config.FLASK_DEBUG)))
        SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE")
        SESSION_COOKIE_SECURE = eval(
            os.getenv("SESSION_COOKIE_SECURE", str(Config.SESSION_COOKIE_SECURE))
        )

        JWT_SECRET_KEY = SECRET_KEY

        IMPORT_PATH = os.getenv("IMPORT_PATH", "import")
        DATA_PATH = os.getenv("DATA_PATH", "data")
        UPLOAD_PATH = os.getenv("UPLOAD_PATH", "uploads")
        FRONTEND_PATH = Path(os.getenv("FRONTEND_PATH", Config.FRONTEND_PATH))
        BEDTOOLS_TMP_PATH = os.getenv("BEDTOOLS_TMP_PATH", Config.BEDTOOLS_TMP_PATH)

        LOGGING = get_logging(FLASK_DEBUG)

    global _config
    _config = _Config
