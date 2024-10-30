.. _installation:

Installation
============

General setup
-------------

Consult the `Flask CLI - Setup <https://dieterich-lab.github.io/scimodom/flask.html#setup>`_ section of the documentation for additional details.

Data import
^^^^^^^^^^^

At launch time, the app uses files defined in ``SetupService`` to populate the database. These files **must** exist and be located under ``IMPORT_PATH`` (development) or ``HOST_IMPORT_DIR`` (production). By default, this path is located under *server/import*, and can be specified in the environment file.

Project and data management
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When the application is up and running, assembly and annotation files must be added before any modification data can be uploaded to the database.
Modification data is organised into projects and datasets, and must be formatted according to the `bedRMod specifications <https://dieterich-lab.github.io/scimodom/bedrmod.html>`_. Consult the `Data management <https://dieterich-lab.github.io/scimodom/database.html#data-management>`_ section of the documentation
for more details.

Dependencies
^^^^^^^^^^^^

Sci-ModoM depends on `Bedtools <https://bedtools.readthedocs.io/en/latest/>`_ v2.31.0. There is nothing to do for production. The version is specified in the `Dockerfile <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/docker/app_container/Dockerfile>`_. For development, it is recommended to use `pre-compiled binaries <https://bedtools.readthedocs.io/en/latest/content/installation.html#downloading-a-pre-compiled-binary>`_ with the correct version number.

Production setup
----------------

The recommended way to run Sci-ModoM in production is to use Podman to create, manage, and deploy the application and the database containers, see `Container setup <https://dieterich-lab.github.io/scimodom/containers.html>`_ for details.

Development setup
-----------------

Database setup
^^^^^^^^^^^^^^

Set up a MariaDB database. One way to do this is to run a MariaDB container image, see `Container setup <https://dieterich-lab.github.io/scimodom/containers.html>`_, in particular the *General* and *Development setup* sections.

Server setup
^^^^^^^^^^^^

Create a Python3 virtual environment and activate it:

.. code-block:: bash

  python3 -m venv ~/.virtualenvs/scimodom
  source ~/.virtualenvs/scimodom/bin/activate

Get the source code and install:

.. code-block:: bash

  git clone https://github.com/dieterich-lab/scimodom.git
  cd scimodom/server
  pip install --upgrade pip setuptools
  pip --verbose install -e '.[dev,tests,docs]' 2>&1 | tee install.log


.. note::

  The package depends on `mysqlclient <https://pypi.org/project/mysqlclient/>`_. You may have to install MySQL development headers and libraries!

Set up your environment configuration in *server/.env*:


.. code-block:: bash

  DATABASE_URI=mysql+mysqldb://scimodom:PASSWORD@127.0.0.1:3307/scimodom
  SECRET_KEY=SECRET_KEY
  SESSION_COOKIE_SAMESITE=None
  SESSION_COOKIE_SECURE=True
  SMTP_SERVER=mail-server.my-site.org
  SMTP_FROM_ADDRESS=scimodom@my-site.org
  NOTIFICATION_ADDRESS=scimodom@my-site.org
  HTTP_PUBLIC_URL=http://localhost:5173/
  UPLOAD_PATH=/path/to/upload
  DATA_PATH=/path/to/data
  BEDTOOLS_TMP_PATH=/path/to/tmp

where ``PASSWORD`` is the password for the scimodom user for the MariaDB database in *docker/secrets/mariadb-scimodom*, ``3307`` is the ``MARIADB_DEV_PORT``
(we recommend to use a non-standard port *e.g.* 3307 to avoid clashes with a local MariaDB/MySQL installation), and ``SECRET_KEY`` is the key found in
*docker/secrets/flask-secret*, see `Container setup <https://dieterich-lab.github.io/scimodom/containers.html>`_ for details. You need to adjust the paths, and make sure they are valid and exist.

.. hint::

  If the host name *localhost* is used in the ``DATABASE_URI``, the database driver will assume that the database is contacted using a named
  socket. That will not work if a container is used!

You can also create a *server/.flaskenv* file with Flask-only variables:

.. code-block:: bash

  FLASK_APP=src/scimodom/app
  FLASK_DEBUG=True

Running the application
"""""""""""""""""""""""

Start the database container under the *docker* directory, see `Container setup - Development setup <https://dieterich-lab.github.io/scimodom/containers.html#development-setup>`_.
Under the *server* directory, initialize the database schema:

.. code-block:: bash

  alembic upgrade head

and start the API backend:

.. code-block:: bash

  flask run

Most Python IDEs can run this process in the integrated debugger. You are now ready to add assemblies, annotations, projects, and data (see
General setup above).

Email functionality, local login and registration
"""""""""""""""""""""""""""""""""""""""""""""""""

To register in development mode, use the *Sign up* button. This requires a functional email server. You first need build the frontend (see Client setup below). Once you receive a link via email, click on this link, but change the frontend server address to that of the Flask development server URL, *e.g.* change *http://localhost:5173/* to *http://localhost:5000*. This is only necessary if you run the database using a container and connect it with the local Flask application.

Note that email functionality may be limited, as your mail server must be willing to relay emails for your ``SMTP_FROM_ADDRESS``, *e.g.* Google or Gmail addresses will most likely not work. This may be problematic if you wish to register, as registration is done via a link sent by email. One way to avoid this problem is to patch the database. Open a python console under your environment and do the following

.. code-block:: python

  from werkzeug.security import generate_password_hash
  generate_password_hash("mypassword", method="pbkdf2")
  # this will return e.g. 'pbkdf2:sha256:600000$vpYjirPAT8xBuPHo$1001474730f96085cdafbf0f159d12e20ec36342b4faddbf226d637c695ee642'

Then go to the database, see *e.g.* `Container setup - Manual database connection <https://dieterich-lab.github.io/scimodom/containers.html#development-setup>`_ and do the following:

.. code-block:: mysql

  INSERT INTO user (email, state, password_hash) VALUES ('test@uni-heidelberg', 'active', 'pbkdf2:sha256:600000$vpYjirPAT8xBuPHo$1001474730f96085cdafbf0f159d12e20ec36342b4faddbf226d637c695ee642');


A new user is now registered, and you can login using whatever email address you used *e.g.* "test@uni-heidelberg" with the chosen password *e.g.* "mypassword".

Client setup
^^^^^^^^^^^^

The first time, you need to install the local packages that the project needs, go to the *client* directory and execute:

.. code-block:: bash

  npm install

This creates a *node_modules* folder. You are now ready to bring up the frontend

.. code-block:: bash

  npm run dev

The application is now available at *http://localhost:5173/*, and any change you make *e.g.* to the HTML code will be reflected in the page you see in your browser.

To test the bundled frontend, run:

.. code-block:: bash

  npm run build


This will populate the folder *dist* with the bundled static HTML/JavaScript code as it should be deployed in production.
The server can now also serve this code. The complete application is now also available under the Flask development server URL *e.g.* at *http://127.0.0.1:5000*.

Development hints
^^^^^^^^^^^^^^^^^

Pre-commit and static type checker
""""""""""""""""""""""""""""""""""

Under the *server* directory:

.. code-block:: bash

  # the first time, you might have to
  pre-commit install
  # the first time pre-commit runs on a file it will automatically download, install, and run the hook
  # runs on all file at commit or run manually
  pre-commit run --all-files
  # to run individual hooks use pre-commit run <hook_id>

  # run static type checker
  mypy -p scimodom

Tests
"""""

To execute the tests, run under the *server* directory:

.. code-block:: bash

  pytest tests

Test automation
"""""""""""""""

The Bedtools version is specified in the `Jenkinsfile <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/Jenkinsfile>`_.

Database schema updates
"""""""""""""""""""""""

The database schema is tracked using Alembic. Changes to the database must be coded at two locations:

- The model must be updated in *server/src/scimodom/database/models.py*
- An Alembic migration script under *server/migrations/versions*

Any change to the schema is generally tracked with:

.. code-block:: bash

  alembic revision [--autogenerate] -m "message"
  alembic upgrade head
