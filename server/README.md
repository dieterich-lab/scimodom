# server

Server side.

### Install

```bash
python3 -m venv server
source server
pip install Flask Flask-Cors SQLAlchemy mysqlclient alembic
```

For development,

```bash
pip install pre-commit
pre-commit install
```

### Database

An empty database is created. This will be used to connect via SQLAlchemy.

```mysql
-- access granted to 'user'@'localhost' to login w/o password
-- mysql
SHOW DATABASES;
USE scimodom;
```
