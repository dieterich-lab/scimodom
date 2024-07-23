FROM docker.io/python:3.11-bookworm

EXPOSE 8000

COPY server/. /install/
COPY client/dist/. /frontend/
COPY docker/app_container/files/. /app/

RUN apt-get update \
    && apt-get install -y bedtools findutils \
    && useradd -g 0 app \
    && mkdir -p /uploads /app/venv \
    && chown -R app /uploads /install /app/venv \
    && cp -r /install/migrations /install/alembic.ini /app

USER app

RUN python3 -m venv /app/venv \
    && . /app/venv/bin/activate \
    && pip install --upgrade pip \
    && pip install wheel \
    && pip install gunicorn \
    && cd /install \
    && pip install .

USER root

RUN rm -rf /install /var/lib/apt/lists/* /tmp/*

ENTRYPOINT /app/entry_point.py
