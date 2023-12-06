# SCIMODOM

## Production Setup

The recommended way to run the application in production is a container setup.
See docker/CONTAINER_SETUP.md for details.

## Development Setup

Create a Python virtual environment witth your preferred method and activate it, e.g.:

```bash
python3 -m venv ~/.virtualenvs/scimodom
. ~/.virtualenvs/scimodom/bin/activate
```

Get the source code from via git:

```bash
git clone https://github.com/dieterich-lab/scimodom.git
cd scimodom
```

Install the applications and it's dependencies editable:

```bash
pip install -e '.[test]'
```

Set up a MariaDB database. One way to do this, is to run a MariaDB
container image. See the 'Development Setup' section in
docker/CONTAINER_SETUP.md how to do this. A local  MariaDB database
is also possible with simular steps. In any case following steps are required:

* Create a database - usually called 'scimodom'.
* Create a database user - usually also called 'scimodom'.
* Grant access to the database to this user.

Set up your environment configuration in server/.env like this:

```
DATABASE_URI=mysql+mysqldb://scimodom:*some password*@127.0.0.1:3306/scimodom
SECRET_KEY=*some secret*
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
UPLOAD_PATH=/path/to/upload
```

**Important:** If the host name 'localhost' is used in the DATABASE_URI the
database driver will assume that the database be contacted using a named
socket. That will not work if a container is used.

Now the database schema can be initialized by executing this command in the 'server' folder:

```bash
alembic upgrade head
```

The application can be started with in server folder like this:

```bash
flask run
```

It will be available at http://127.0.0.1:5000.

