#!/bin/sh

set -eu

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
env_file="$script_path/../.env_docker"
. "$env_file"

"$DOCKER" build . -t "$DB_IMAGE_NAME"
