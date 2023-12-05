import os
import logging

from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Set Flask and logging variables.

    :param parent_dir: Parent directory (package)
    :type parent_dir: Path | str
    :param import_dir: Import directory (package)
    :type import_dir: Path | str
    """

    CWD = Path(__file__).absolute()
    if os.getenv("LOCAL_APP"):
        env_file = Path(CWD.parent.parent.parent, ".env.local")
        LOCAL_APP = True
    else:
        env_file = Path(CWD.parent.parent.parent, ".env.development")
        LOCAL_APP = False
    load_dotenv(env_file)
    FLASK_DEBUG = eval(os.getenv("FLASK_DEBUG", "False"))
    DATABASE_URI = os.getenv("DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE")

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
        parent_dir: str | Path | None = None,
        import_dir: str | Path | None = None,
    ) -> None:
        """Constructor method.

        Note: Default tables from import directory, no check.
        """
        if parent_dir is None:
            parent_dir = self.CWD.parent.parent.parent

        if import_dir is None:
            import_dir = "import"
        self.import_dir: Path = Path(parent_dir, import_dir)

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
