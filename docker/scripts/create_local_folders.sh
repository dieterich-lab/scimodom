#!/bin/bash

# We don't want to bother container user sto install Python packages.
# So we simulate here the dotenv package by a shell wrapper.

set -eu

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
env_file="$script_path/../.env"

. "$env_file"

export HOST_BACKUP_DIR HOST_SECRETS_DIR HOST_IMPORT_DIR HOST_DB_DATA_DIR

exec "$script_path/__create_local_folders.py"