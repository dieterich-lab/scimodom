#!/bin/bash

set -eu

export MYSQL_PWD=$(cat $MARIADB_ROOT_PASSWORD_FILE)
gunzip -c /backup/all-databases.sql.gz \
  | mariadb -uroot
