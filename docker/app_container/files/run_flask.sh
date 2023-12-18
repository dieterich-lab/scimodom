#!/bin/bash

echo '### Activating venv ###'
. /app/venv/bin/activate
cd /app
echo '### Upgrading Database ###'
alembic upgrade head
# ad hoc - TODO
upsert --all
echo '### Starting gunicorn ###'
exec gunicorn -b 0.0.0.0:8000 -w $1 'scimodom.app:create_app()'
