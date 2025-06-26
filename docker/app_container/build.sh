#!/bin/sh

set -eu

script_path="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
env_file="$script_path/../.env_docker"
. "$env_file"

cd "$script_path/../../client"
npm install
npm run build

cd "$script_path/../.."
BUILD_TAG="$(git describe --tags --always --dirty 2>/dev/null || echo unknown)"
BUILD_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
BUILD_COMMIT_DATE="$(git log -1 --format=%aI 2>/dev/null || echo unknown)"
"$DOCKER" build . \
          --build-arg BUILD_TAG="$BUILD_TAG" \
          --build-arg BUILD_COMMIT="$BUILD_COMMIT" \
          --build-arg BUILD_COMMIT_DATE="$BUILD_COMMIT_DATE" \
          -t "$APP_IMAGE_NAME" \
          -f docker/app_container/Dockerfile
