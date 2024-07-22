#!/bin/bash

set -e -u

. .env

sleep_seconds=600
max_age_minutes=60

if [[ -z $UPLOAD_PATH ]]
then
    echo 'mini_cron.sh: No $UPLOAD_PATH - aborting.'
    exit 1
fi
if [[ -z $BEDTOOLS_TMP_PATH ]]
then
    echo 'mini_cron.sh: No $BEDTOOLS_TMP_PATH - aborting.'
    exit 1
fi

while [[ 1 = 1 ]]
do
    for path_to_clean in "$UPLOAD_PATH" "$BEDTOOLS_TMP_PATH"
    do
        if [[ -d $path_to_clean ]]
        then
            find "$path_to_clean" -type f -mmin +${max_age_minutes} -delete
        fi
    done
    sleep $sleep_seconds
done
