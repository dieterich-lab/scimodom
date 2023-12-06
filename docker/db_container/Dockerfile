FROM docker.io/mariadb:11.2

COPY scripts/dump_db.sh /scripts/dump_db.sh
COPY scripts/load_db.sh /scripts/load_db.sh

RUN chmod 755 /scripts/dump_db.sh /scripts/load_db.sh
