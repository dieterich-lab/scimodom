#!/usr/bin/python3
from os import umask
from pathlib import Path
from os.path import dirname, join
from random import randrange
from sys import stderr

SCRIPT_DIR = dirname(__file__)
SECRETS_FOLDER = join(dirname(SCRIPT_DIR), 'secrets')
SECRET_FILES = ['mariadb-root', 'mariadb-scimodom', 'flask-secret']

BACKUP_FOLDER = join(dirname(SCRIPT_DIR), 'backup')
DATA_FOLDER = join(dirname(SCRIPT_DIR), 'db_data')

HOST_FOLDERS = [SECRETS_FOLDER, BACKUP_FOLDER, DATA_FOLDER]

PASSWORD_LENGTH = 32

ALLOWED_PASSWORD_CHARS = [
    chr(c)
    for c in [
        *range(ord('a'), ord('z')+1),
        *range(ord('A'), ord('Z')+1),
        *range(ord('0'), ord('9')+1),
    ]
]


def get_random_string():
    chars = [
        ALLOWED_PASSWORD_CHARS[randrange(0, len(ALLOWED_PASSWORD_CHARS))]
        for _ in range(PASSWORD_LENGTH)
    ]
    return ''.join(chars)


def write_password_file(name):
    path = join(SECRETS_FOLDER, name)
    if Path(path).exists():
        print(f"Ignoring '{path}' - exists already.", file=stderr)
        return
    with open(path, 'w') as fp:
        print(get_random_string(), file=fp)


umask(0o77)
for folder in HOST_FOLDERS:
    Path(folder).mkdir(exist_ok=True)
for name in SECRET_FILES:
    write_password_file(name)
