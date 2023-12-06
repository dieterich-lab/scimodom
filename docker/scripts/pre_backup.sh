#!/bin/bash

set -eu

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
env_file="$script_path/../.env"

. "$env_file"

"$DOCKER" exec "$DB_CONTAINER_NAME" /scripts/dump_db.sh
