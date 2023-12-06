import os
import logging

from pathlib import Path
from dotenv import load_dotenv


DEFAULT_FRONTEND_PATH = Path(__file__).parent.parent.parent.parent.joinpath('client').joinpath('dist')


class Config:
    """Set Flask and logging variables.

    :param import_dir: Import directory (package)
    :type import_dir: Path | str
    """

    ENV_FILE = os.getenv('ENV_FILE', '.env')
    load_dotenv(ENV_FILE)
    FLASK_DEBUG = eval(os.getenv("FLASK_DEBUG", "False"))
    DATABASE_URI = os.getenv("DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE")
    IMPORT_PATH = os.getenv("IMPORT_PATH", "import")
    FRONTEND_PATH = Path(os.getenv("FRONTEND_PATH", DEFAULT_FRONTEND_PATH))

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
        self.method_tbl: tuple[str, Path] = (
            "DetectionMethod",
            Path(self.import_dir, "method.csv"),
        )
