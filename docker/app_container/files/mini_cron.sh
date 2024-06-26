#!/bin/bash

set -e -u

. .env

sleep_seconds=600
upload_max_age_minutes=60

if [[ -z $UPLOAD_PATH ]]
then
    echo 'mini_cron.sh: No $UPLOAD_PATH - aborting.'
    exit 1
fi

mkdir -p "$BEDTOOLS_TMP_PATH"
chmod 1777 "$BEDTOOLS_TMP_PATH"

while [[ 1 = 1 ]]
do
    find "$UPLOAD_PATH" "$BEDTOOLS_TMP_PATH" -type f -mmin +${upload_max_age_minutes} -delete
    sleep $sleep_seconds
done
