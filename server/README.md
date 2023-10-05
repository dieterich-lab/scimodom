# server

Server side.

### Install

```bash
python3 -m venv server
source server
pip install Flask Flask-Cors SQLAlchemy mysqlclient alembic
# check environment.yml
```

```bash
git clone https://github.com/dieterich-lab/scimodom.git
cd scimodom
# checkout db
cd server
pip --verbose install -e .[tests,docs] 2>&1 | tee install.log
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

### Run the app

Create a file _.env.development_ with at least the following

```bash
DATABASE_URI=
SECRET_KEY=
```

then

```bash
flask run
```
