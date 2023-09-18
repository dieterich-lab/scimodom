import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Set Flask config variables"""

    def __init__(self, parent_dir=None, import_dir=None):
        cwd = Path(__file__).absolute()
        if parent_dir is None:
            parent_dir = cwd.parent.parent.parent

        if import_dir is None:
            import_dir = Path(parent_dir, "import")

    # move .env files to parent directory?
    # class is not instantiated by app
    if os.getenv("LOCAL_APP"):
        env_file = ".env.local"
    else:
        env_file = ".env.development"
    load_dotenv(env_file)

    FLASK_DEBUG = os.getenv("FLASK_DEBUG")
    DATABASE_URI = os.getenv("DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE")
