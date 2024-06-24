#!/bin/bash

echo '### Activating venv ###'
. /app/venv/bin/activate
cd /app
echo '### Upgrading Database ###'
alembic upgrade head
echo '### Starting gunicorn ###'
extra_opts=''
if [[ -n $3 ]]
then
  extra_opts="--forwarded-allow-ips=$3"
fi
exec gunicorn -b 0.0.0.0:8000 -w $1 --timeout $2 $extra_opts 'scimodom.app:create_app()'
