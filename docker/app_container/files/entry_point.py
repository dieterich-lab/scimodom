#!/usr/bin/python3

from os import system, environ

SECRETS_FOLDER = '/run/secrets'
ENV_FILE_NAME = '/app/.env'
FLASK_SECRET_FILE = f"{SECRETS_FOLDER}/flask-secret"
DATABASE_PASSWORD_FILE = f"{SECRETS_FOLDER}/mariadb-scimodom"


def write_env_file():
    db_password = get_secret(DATABASE_PASSWORD_FILE)
    flask_secret = get_secret(FLASK_SECRET_FILE)
    with open(ENV_FILE_NAME, 'w') as fp:
        print(f"""
DATABASE_URI=mysql+mysqldb://scimodom:{db_password}@scimodom_db:3306/scimodom
SECRET_KEY={flask_secret}
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
UPLOAD_PATH=/uploads
IMPORT_PATH=/import
FRONTEND_PATH=/frontend
""", file=fp)


def get_secret(path):
    with open(path) as fp:
        return fp.readline().strip()


write_env_file()
system(f"exec su - app /app/run_flask.sh {environ.get('HTTP_WORKER_PROCESSES')}")
