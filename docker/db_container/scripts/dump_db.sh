#!/bin/bash

set -eu

export MYSQL_PWD=$(cat $MARIADB_ROOT_PASSWORD_FILE)
mariadb-dump --all-databases -uroot >/backup/all-databases.sql
[[ -f /backup/all-databases.sql.gz ]] && rm /backup/all-databases.sql.gz
gzip /backup/all-databases.sql
