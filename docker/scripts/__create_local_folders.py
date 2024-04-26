#!/usr/bin/python3
from os import umask, environ, chmod
from pathlib import Path
from os.path import join
from random import randrange
from sys import stderr

HOST_BACKUP_DIR = environ.get("HOST_BACKUP_DIR")
HOST_SECRETS_DIR = environ.get("HOST_SECRETS_DIR")
HOST_CONFIG_DIR = environ.get("HOST_CONFIG_DIR")
HOST_DB_DATA_DIR = environ.get("HOST_DB_DATA_DIR")
HOST_IMPORT_DIR = environ.get("HOST_IMPORT_DIR")
HOST_DATA_DIR = environ.get("HOST_DATA_DIR")

HOST_FOLDERS = [
    HOST_BACKUP_DIR,
    HOST_SECRETS_DIR,
    HOST_CONFIG_DIR,
    HOST_DB_DATA_DIR,
    HOST_IMPORT_DIR,
    HOST_DATA_DIR,
    Path(HOST_DATA_DIR, "metadata"),
    Path(HOST_DATA_DIR, "metadata", "project_requests"),
    Path(HOST_DATA_DIR, "annotation"),
    Path(HOST_DATA_DIR, "assembly"),
]
SECRET_FILES = ["mariadb-root", "mariadb-scimodom", "flask-secret"]

PASSWORD_LENGTH = 32

ALLOWED_PASSWORD_CHARS = [
    chr(c)
    for c in [
        *range(ord("a"), ord("z") + 1),
        *range(ord("A"), ord("Z") + 1),
        *range(ord("0"), ord("9") + 1),
    ]
]


def get_random_string():
    chars = [
        ALLOWED_PASSWORD_CHARS[randrange(0, len(ALLOWED_PASSWORD_CHARS))]
        for _ in range(PASSWORD_LENGTH)
    ]
    return "".join(chars)


def write_password_file(filename):
    path = join(HOST_SECRETS_DIR, filename)
    if Path(path).exists():
        print(f"Ignoring '{path}' - exists already.", file=stderr)
        return
    with open(path, "w") as fp:
        print(get_random_string(), file=fp)


def write_client_config():
    path = join(HOST_CONFIG_DIR, "config.js")
    url = environ.get("HTTP_PUBLIC_URL")
    with open(path, "w") as fp:
        print(f"export const API_BASE_URL = '{url}/api/v0/';", file=fp)
    chmod(path, 0o644)


umask(0o77)
for folder in HOST_FOLDERS:
    Path(folder).mkdir(exist_ok=True)
for name in SECRET_FILES:
    write_password_file(name)
write_client_config()
Path(HOST_IMPORT_DIR).chmod(0o755)
