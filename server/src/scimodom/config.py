import datetime
import logging
import os
from pathlib import Path
from typing import ClassVar

from dotenv import load_dotenv

DEFAULT_FRONTEND_PATH = (
    Path(__file__).parent.parent.parent.parent.joinpath("client").joinpath("dist")
)


class MissingEnviron(Exception):
    """Exception handling for missing environment variable."""

    pass


class Config:
    """Set Flask and logging variables.

    :param import_dir: Import directory (package)
    :type import_dir: Path | str
    """

    ENV_FILE: ClassVar[str] = os.getenv("ENV_FILE", ".env")
    load_dotenv(ENV_FILE)

    try:
        DATABASE_URI: ClassVar[str] = os.environ["DATABASE_URI"]
        SECRET_KEY: ClassVar[str] = os.environ["SECRET_KEY"]
    except KeyError:
        msg = (
            "Undefined environment variable(s): DATABASE_URI and/or SECRET_KEY. "
            "Check your .env file!"
        )
        raise MissingEnviron(msg)

    try:
        SMTP_SERVER: ClassVar[str] = os.environ["SMTP_SERVER"]
        SMTP_FROM_ADDRESS: ClassVar[str] = os.environ["SMTP_FROM_ADDRESS"]
        PUBLIC_URL: ClassVar[str] = os.environ["PUBLIC_URL"]
    except KeyError:
        msg = (
            "Undefined environment variable(s): SMTP_SERVER, SMTP_FROM_ADDRESS, and/or PUBLIC_URL. "
            "Check your .env file!"
        )
        raise MissingEnviron(msg)

    FLASK_DEBUG: ClassVar[bool] = eval(os.getenv("FLASK_DEBUG", "False"))
    SESSION_COOKIE_SAMESITE: ClassVar[str | None] = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE: ClassVar[bool] = eval(
        os.getenv("SESSION_COOKIE_SECURE", "True")
    )

    JWT_SECRET_KEY: ClassVar[str | None] = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)

    IMPORT_PATH: ClassVar[str | Path] = os.getenv("IMPORT_PATH", "import")
    DATA_PATH: ClassVar[str | Path] = os.getenv("DATA_PATH", "data")
    FRONTEND_PATH: ClassVar[Path] = Path(
        os.getenv("FRONTEND_PATH", DEFAULT_FRONTEND_PATH)
    )

    LOGGING = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            "default": {
                "format": "[%(asctime)s:%(msecs)03d] %(levelname)s %(name)s.%(funcName)s.%(lineno)d | %(message)s"
                if FLASK_DEBUG
                else "[%(asctime)s] %(levelname)s %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        handlers={
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": logging.DEBUG if FLASK_DEBUG else logging.INFO,
            }
        },
        root={
            "handlers": ["default"],
            "level": logging.DEBUG if FLASK_DEBUG else logging.INFO,
        },
    )

    def __init__(
        self,
        import_dir: str | Path | None = None,
    ) -> None:
        """Constructor method.

        Note: Default tables from import directory, no check.
        """

        if import_dir is None:
            self.import_dir = self.IMPORT_PATH
        else:
            self.import_dir = import_dir

        self.modomics_tbl: tuple[str, Path] = (
            "Modomics",
            Path(self.import_dir, "modomics.csv"),
        )
        self.taxonomy_tbl: tuple[str, Path] = (
            "Taxonomy",
            Path(self.import_dir, "taxonomy.csv"),
        )
        self.ncbi_taxa_tbl: tuple[str, Path] = (
            "Taxa",
            Path(self.import_dir, "ncbi_taxa.csv"),
        )
        self.assembly_tbl: tuple[str, Path] = (
            "Assembly",
            Path(self.import_dir, "assembly.csv"),
        )
        self.assembly_version_tbl: tuple[str, Path] = (
            "AssemblyVersion",
            Path(self.import_dir, "assembly_version.csv"),
        )
        self.annotation_tbl: tuple[str, Path] = (
            "Annotation",
            Path(self.import_dir, "annotation.csv"),
        )
        self.annotation_version_tbl: tuple[str, Path] = (
            "AnnotationVersion",
            Path(self.import_dir, "annotation_version.csv"),
        )
        self.method_tbl: tuple[str, Path] = (
            "DetectionMethod",
            Path(self.import_dir, "method.csv"),
        )
