# Sci-ModoM

## Production Setup

The recommended way to run the application in production is a container setup.
See docker/CONTAINER_SETUP.md for details.

## Development Setup

### Overview

The application consists of the following components:

* Database: MaraiDB
* Server: A Web-API backend based on Python with Flask
* Client: A Web-GUI written JavaScript bades on VUE.js

To do development all components can be run locally.

### DEV Database Setup

Set up a MariaDB database. One way to do this, is to run a MariaDB
container image. See the 'Development Setup' section in
docker/CONTAINER_SETUP.md how to do this. A local  MariaDB database
is also possible with simular steps. In any case following steps are required:

* Create a database - usually called 'scimodom'.
* Create a database user - usually also called 'scimodom'.
* Grant access to the database to this user.

### DEV Server Setup

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

The API backend can be started with in server folder like this:

```bash
flask run
```

Must Python IDEs can run this process also in the integrated debugger.

### DEV Client Setup

To bring up the frontend go to the client folder and execute there:

```bash
npm install
npm run dev
```

Now the application is available here:

* http://localhost:5173/

To test the bundled frontend run in the client folder:

```bash
npm install
npm run build
```

This will populate the folder client/dist with the bundled static
HTML/JavaScript code as it should be deployed in production.
The server can now also serve this code. The complete application
is now also available under the Flask develpment server URL:

* http://127.0.0.1:5000

## Development Hints

### Database Schema Updates

The database schema is tracked using Alembic any changes to the database
must be coded at two locations:

* An Alembic version must be defined in server/migrations/versions
* The model must be updated in server/src/scimodom/database/models.py

### Tests

To execute the Python tests run in the server folder:

```bash
pytest tests
```
## License

`scimodom` is licensed under the GNU Affero General Public Licence (AGPL) version 3.
See `LICENSE` file for details.
