# Sci-ModoM

## Production Setup

The recommended way to run the application in production is a container setup. See [Container Setup](docker/CONTAINER_SETUP.md) for details.

## Development Setup

### Overview

The application consists of the following components:

- Database: MariaDB
- Server: A REST-API backend using Python3 and Flask
- Client: A Web-GUI using Vue.js

All components can be run locally.

### Pre-commit hooks and static code analyses

For development:

```bash
pip install pre-commit
pre-commit install
# runs on all file at commit or pre-commit run

pip install sqlalchemy[mypy]
# run static type checker after install
mypy -p scimodom
```

### Database setup

Set up a MariaDB database. One way to do this is to run a MariaDB container image. See the _Development Setup_ section in [Container Setup](docker/CONTAINER_SETUP.md) on how to do this. A local MariaDB database is also possible with similar setup steps. The following steps are required:

- Create a database
- Create a database user
- Grant access to the database to this user

### Server setup

Create a Python3 virtual environment with your preferred method and activate it, _e.g._:

```bash
python3 -m venv ~/.virtualenvs/scimodom
. ~/.virtualenvs/scimodom/bin/activate
```

Get the source code and install :

```bash
git clone https://github.com/dieterich-lab/scimodom.git
cd scimodom
pip install --upgrade pip setuptools
pip --verbose install -e '.[test]' 2>&1 | tee install.log
```

Set up your environment configuration in _server/.env_ like this:

```
DATABASE_URI=mysql+mysqldb://scimodom:*some password*@127.0.0.1:3306/scimodom
SECRET_KEY=*some secret*
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
UPLOAD_PATH=/path/to/upload
DATA_PATH=/path/to/data
```

**Important:** If the host name _localhost_ is used in the `DATABASE_URI` the database driver will assume that the database is contacted using a named
socket. That will not work if a container is used!

Now the database schema can be initialized by executing this command under the _server_ directory:

```bash
alembic upgrade head
```

The API backend can be started with:

```bash
# under client/server
flask run
```

Most Python IDEs can run this process in the integrated debugger.

### Client setup

To bring up the frontend, go to the _client_ directory and execute:

```bash
npm install
npm run dev
```

Now the application is available here:

- http://localhost:5173/

To test the bundled frontend, run under the _client_ directory:

```bash
npm run build
```

This will populate the folder _client/dist_ with the bundled static HTML/JavaScript code as it should be deployed in production.
The server can now also serve this code. The complete application is now also available under the Flask development server URL:

- http://127.0.0.1:5000

## Development Hints

### Database schema updates

The database schema is tracked using Alembic. Changes to the database must be coded at two locations:

- An Alembic version must be defined in server/migrations/versions
- The model must be updated in server/src/scimodom/database/models.py

Any change to the schema is generally tracked with:

```bash
# under client/server
alembic revision --autogenerate [-m "message"]
alembic upgrade head
```

### Tests

To execute the Python tests run under the _server_ directory:

```bash
pytest tests
```

## License

GNU Affero General Public Licence (AGPL) version 3.
