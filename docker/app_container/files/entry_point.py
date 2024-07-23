#!/usr/bin/python3

from os import system, environ

SECRETS_FOLDER = "/run/secrets"
ENV_FILE_NAME = "/app/.env"
FLASK_SECRET_FILE = f"{SECRETS_FOLDER}/flask-secret"
DATABASE_PASSWORD_FILE = f"{SECRETS_FOLDER}/mariadb-scimodom"

SMTP_SERVER = environ.get("SMTP_SERVER")
SMTP_FROM_ADDRESS = environ.get("SMTP_FROM_ADDRESS")
NOTIFICATION_ADDRESS = environ.get("NOTIFICATION_ADDRESS")
HTTP_PUBLIC_URL = environ.get("HTTP_PUBLIC_URL")


def write_env_file():
    db_password = get_secret(DATABASE_PASSWORD_FILE)
    flask_secret = get_secret(FLASK_SECRET_FILE)
    with open(ENV_FILE_NAME, "w") as fp:
        print(
            f"""
DATABASE_URI=mysql+mysqldb://scimodom:{db_password}@scimodom_db:3306/scimodom
SECRET_KEY={flask_secret}
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
SMTP_SERVER={SMTP_SERVER}
SMTP_FROM_ADDRESS={SMTP_FROM_ADDRESS}
NOTIFICATION_ADDRESS={NOTIFICATION_ADDRESS}
HTTP_PUBLIC_URL={HTTP_PUBLIC_URL}
UPLOAD_PATH=/uploads
IMPORT_PATH=/import
DATA_PATH=/data
FRONTEND_PATH=/frontend
BEDTOOLS_TMP_PATH=/tmp/bedtools
""",
            file=fp,
        )


def get_secret(path):
    with open(path) as fp:
        return fp.readline().strip()


write_env_file()
system("cd /app && /app/mini_cron.sh &")
system("find /uploads /import /data -exec chown app {} \\;")
system("find /uploads /import /data -exec chgrp 0 {} \\;")
system("find /uploads /import /data -exec chmod g+wr,o-rwx {} \\;")
system("find /uploads /import /data -type d -exec chmod g+xs {} \\;")
system(
    f"exec su - app /app/run_flask.sh {environ.get('HTTP_WORKER_PROCESSES')} {environ.get('HTTP_WORKER_TIMEOUT', 30)}"
    f" {environ.get('HTTP_REVERSE_PROXY_IPS', '')}"
)
