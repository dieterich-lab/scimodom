# Sci-ModoM

## Overview

The application consists of the following components:

- Database: MariaDB
- Server: A REST-API backend using Python3 and Flask
- Client: A Web-GUI using Vue.js

### General setup

At lauchtime, the app uses tables defined in `SetupService` to populate the database. These tables **must** exist. They are used both in development and production. They **must** be located under `IMPORT_PATH` (defaults to _server/import_, or specify in _.env_ file).

## Production setup

The recommended way to run Sci-ModoM in production is to use podman compose to create, manage, and deploy the application and the database containers, see [Container Setup](docker/CONTAINER_SETUP.md) for details.

## Development setup

### Database setup

Set up a MariaDB database. One way to do this is to run a MariaDB container image, see the _Development Setup_ section in [Container Setup](docker/CONTAINER_SETUP.md). The following steps are required:

- Create a database
- Create a database user
- Grant access to the database to this user

### Server setup

Create a Python3 virtual environment with your preferred method and activate it _e.g._:

```bash
python3 -m venv ~/.virtualenvs/scimodom
. ~/.virtualenvs/scimodom/bin/activate
```

Get the source code and install :

```bash
git clone https://github.com/dieterich-lab/scimodom.git
cd scimodom
pip install --upgrade pip setuptools
pip --verbose install 2>&1 | tee install.log
```

**Note:** The package depends on [mysqlclient](https://pypi.org/project/mysqlclient/). You may have to install MySQL development headers and
libraries before. You also need a working installation of [Bedtools](https://bedtools.readthedocs.io/en/latest/), _e.g._
[pre-compiled binaries](https://bedtools.readthedocs.io/en/latest/content/installation.html#downloading-a-pre-compiled-binary).

Set up your environment configuration in _server/.env_ like this:

```
DATABASE_URI=mysql+mysqldb://scimodom:*some password*@127.0.0.1:3306/scimodom
SECRET_KEY=*some secret*
SESSION_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
UPLOAD_PATH=/path/to/upload
DATA_PATH=/path/to/data
BEDTOOLS_TMP_PATH=path/to/bedtools_tmp
SMTP_SERVER=outgoing-email-server.my-site.org
SMTP_FROM_ADDRESS=sci-modom-admin@my-site.org
NOTIFICATION_ADDRESS=notification-email@my-site.org
HTTP_PUBLIC_URL=https://sci-modom.my-site.org
```

**Important:** If the host name _localhost_ is used in the `DATABASE_URI` the database driver will assume that the database is contacted using a named
socket. That will not work if a container is used!

In addition to _server/.env/_, a Flask-specific configuration in _server/.flaskenv_ can be used:

```
FLASK_APP=src/scimodom/app
FLASK_DEBUG=True
```

Now the database container must be started under the _docker_ directory:

```bash
# under scimodom/docker
docker compose -f docker-compose-db-only.yml up -d
```

The database schema can then be initialized by executing this command under the _server_ directory:

```bash
# under scimodom/server
alembic upgrade head
```

The API backend can be started with:

```bash
# under scimodom/server
flask run
```

Most Python IDEs can run this process in the integrated debugger.

### Client setup

To bring up the frontend, go to the _client_ directory and execute:

```bash
# under scimodom/client
npm install # first time install
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

#### Local login

Registration is completed via email. These environment variables are required:

```
SMTP_SERVER=outgoing-email-server.my-site.org
SMTP_FROM_ADDRESS=sci-modom-admin@my-site.org
```

**Important:** Make sure to build the frontend beforehand (see above). After receiving the registration link via email, click on the link, but change the default port `5173` to `5000` to point to the Flask development server URL.

Alternatively, you can patch the database (add user).

### Development hints

For development:

```bash
pip --verbose install -e '.[dev,tests,docs]' 2>&1 | tee install.log
```

#### Pre-commit and static type checker

Under the _server_ directory:

```bash
# first time, you might have to
pre-commit install
# the first time pre-commit runs on a file it will automatically download, install, and run the hook
# runs on all file at commit or run manually
pre-commit run --all-files
# to run individual hooks use pre-commit run <hook_id>

# run static type checker
mypy -p scimodom
```

#### Tests

To execute the Python tests run under the _server_ directory:

```bash
pytest tests
```

To run pytest from command line, adjust the `PYTHONPATH` _e.g._

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/scimodom/server/tests/"
```

#### Database schema updates

The database schema is tracked using Alembic. Changes to the database must be coded at two locations:

- An Alembic version must be defined in server/migrations/versions
- The model must be updated in server/src/scimodom/database/models.py

Any change to the schema is generally tracked with:

```bash
# under client/server
alembic revision --autogenerate [-m "message"]
alembic upgrade head
```

## License

GNU Affero General Public Licence (AGPL) version 3.
