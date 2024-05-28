import datetime
import logging
import os
from pathlib import Path
from sys import stderr
from typing import ClassVar

from dotenv import load_dotenv

DEFAULT_FRONTEND_PATH = (
    Path(__file__).parent.parent.parent.parent.joinpath("client").joinpath("dist")
)


_env_file = None


def _get_required_parameter(name: str):
    try:
        return os.environ[name]
    except KeyError:
        print(
            f"Required parameter '{name}' not set. Please check the file '{_env_file}'.",
            file=stderr,
        )
        exit(1)


class Config:
    """Set Flask and logging variables.

    :param import_dir: Import directory (package)
    :type import_dir: Path | str
    """

    global _env_file
    _env_file = os.getenv("ENV_FILE", ".env")
    ENV_FILE: ClassVar[str] = _env_file
    load_dotenv(_env_file)

    DATABASE_URI: ClassVar[str] = _get_required_parameter("DATABASE_URI")
    SECRET_KEY: ClassVar[str] = _get_required_parameter("SECRET_KEY")
    SMTP_SERVER: ClassVar[str] = _get_required_parameter("SMTP_SERVER")
    SMTP_FROM_ADDRESS: ClassVar[str] = _get_required_parameter("SMTP_FROM_ADDRESS")
    NOTIFICATION_ADDRESS: ClassVar[str] = _get_required_parameter(
        "NOTIFICATION_ADDRESS"
    )
    HTTP_PUBLIC_URL: ClassVar[str] = _get_required_parameter("HTTP_PUBLIC_URL")

    FLASK_DEBUG: ClassVar[bool] = eval(os.getenv("FLASK_DEBUG", "False"))
    SESSION_COOKIE_SAMESITE: ClassVar[str | None] = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE: ClassVar[bool] = eval(
        os.getenv("SESSION_COOKIE_SECURE", "True")
    )

    JWT_SECRET_KEY: ClassVar[str | None] = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=1)

    IMPORT_PATH: ClassVar[str | Path] = os.getenv("IMPORT_PATH", "import")
    DATA_PATH: ClassVar[str | Path] = os.getenv("DATA_PATH", "data")
    UPLOAD_PATH: ClassVar[str | Path] = os.getenv("UPLOAD_PATH", "uploads")
    FRONTEND_PATH: ClassVar[Path] = Path(
        os.getenv("FRONTEND_PATH", DEFAULT_FRONTEND_PATH)
    )
    BEDTOOLS_TMP_PATH: ClassVar[str | Path] = os.getenv(
        "BEDTOOLS_TMP_PATH", "/tmp/bedtools"
    )

    LOGGING = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            "default": {
                "format": "%(asctime)s:%(msecs)03d [%(levelname)s] %(name)s.%(funcName)s.%(lineno)d | %(message)s"
                if FLASK_DEBUG
                else "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        handlers={
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": logging.DEBUG if FLASK_DEBUG else logging.WARNING,
            }
        },
        root={
            "handlers": ["default"],
            "level": logging.DEBUG if FLASK_DEBUG else logging.WARNING,
        },
    )

    def __init__(
        self,
        import_dir: str | Path | None = None,
    ) -> None:
        """Constructor method.

        :param import_dir: start-up import directory
        :type import_dir: str | Path | None
        """

        if import_dir is None:
            self.import_dir = self.IMPORT_PATH
        else:
            self.import_dir = import_dir

        self.rna_tbl: tuple[str, Path] = (
            "RNAType",
            Path(self.import_dir, "rna_type.csv"),
        )
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
