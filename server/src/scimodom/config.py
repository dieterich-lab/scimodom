import os
from dotenv import load_dotenv

if os.getenv("LOCAL_APP"):
    env_file = ".env.local"
else:
    env_file = ".env.development"
load_dotenv(env_file)


class Config:
    """Set Flask config variables"""

    FLASK_DEBUG = os.getenv("FLASK_DEBUG")
    DATABASE_URI = os.getenv("DATABASE_URI")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE")
