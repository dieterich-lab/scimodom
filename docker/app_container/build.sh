#!/bin/sh

set -eu

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
env_file="$script_path/../.env"
. "$env_file"

cd "$script_path/../../client"
npm install
npm run build
cd "$script_path/../.."
$DOCKER build . -t scimodom_app:latest -f docker/app_container/Dockerfile