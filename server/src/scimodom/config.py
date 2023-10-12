import os
import logging
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Set Flask and logging variables"""

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

    def __init__(self, parent_dir=None, import_dir=None):
        if parent_dir is None:
            parent_dir = self.CWD.parent.parent.parent

        if import_dir is None:
            import_dir = Path(parent_dir, "import")
        self.import_dir = import_dir

        self.modomics_tbl = Path(import_dir, "modomics.csv")
        self.taxonomy_tbl = Path(import_dir, "taxonomy.csv")
        self.ncbi_taxa_tbl = Path(import_dir, "ncbi_taxa.csv")
        self.assembly_tbl = Path(import_dir, "assembly.csv")
        self.assembly_version_tbl = Path(import_dir, "assembly_version.csv")
        self.method_tbl = Path(import_dir, "method.csv")
