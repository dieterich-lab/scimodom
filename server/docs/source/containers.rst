.. _containers:

Container setup
===============

Prerequisites
-------------

Container tools
^^^^^^^^^^^^^^^

A container management CLI is required such as ``podman-compose`` or ``docker compose`` (`Compose V2 <https://docs.docker.com/compose/migrate>`_).
Docker Swarm has not been tested and may not work. The following versions are known to work:

- Podman version 4.3.1 with podman-compose version 1.0.3 on Debian 12
- Docker version 27.2.0 with docker compose version 2.29.2 on Debian 12

Podman handles rootless containers.

Image building
^^^^^^^^^^^^^^

Node.js and npm are required to build the container images. Vue.js presently requires Node.js 16 or newer.
The following versions are known to work:

- Node.js version 18.19.0 on Debian 12
- npm version 9.2.0 and 10.8.2 on Debian 12

General setup
-------------

Configure the docker/.env_docker file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a file *.env_docker* in the *docker* directory using `env_docker_example <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/docker/env_docker_example>`_ as template. Environment variables
defined in this file are used to build the images.

Configure the .env file
^^^^^^^^^^^^^^^^^^^^^^^

Create a file *.env* in the same directory as the YAML file used to define the services *i.e.* *docker-compose.yml* or *docker-compose-db-only.yml*, using `env_example <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/server/env_example>`_ as template. This is the environment file used by compose. For development, this file is typically located in the *docker* directory (same location as *.env_docker*), but under production it may be located in a separate deployment directory.

Set up the local directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Under your deployment directory, or under the *docker* directory in development setup, create the directory structure for the database:

.. code-block:: bash

  ./scripts/create_local_folders.sh

In particular, the following files are created:

- **secrets/mariadb-root**: Password for the root user for the MariaDB database.
- **secrets/mariadb-scimodom**: Password for the scimodom user for the MariaDB database.

Production setup
----------------

Build the images
^^^^^^^^^^^^^^^^

.. code-block:: bash

  cd docker/db_container
  ./build.sh
  cd ../app_container
  ./build.sh

Optional: copy to a live instance
"""""""""""""""""""""""""""""""""

If the images are built on a different machine, or if multiple deployments are run on the same container host, the required data must be deployed
to that system or a separate folder per instance.

In case of a deployment to a different container host, the following data need to be transferred:

- The images, *e.g.* via a Docker repository
  - The database image *e.g.* scimodom_db:latest
  - The application image *e.g.* scimodom_app:latest
- The docker/scripts folder and the necessary import tables (import folder)
- The *docker-compose.yml* file
- The *.env* file

If multiple instances are run on the same host, a separate folder needs to be created for each instance. Make sure that the ports, paths and names in the
*.env* files don't collide!

Starting and stopping the containers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

  # or docker compose
  podman-compose -f docker-compose.yml up -d

And to stop:

.. code-block:: bash

  # or docker compose
  podman-compose -f docker-compose.yml down


Development setup
-----------------

The database can be run using a container and connected with the application running locally by using *docker-compose-db-only.yml*. The *.env* file needs a few variables only, see `env_example <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/server/env_example>`_ (database only).

Set up the local directories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For development, running

.. code-block:: bash

  ./scripts/create_local_folders.sh

does not create the development database folder, this must be done manually. The name of this folder matches the value from ``HOST_DEV_DB_DATA_DIR`` defined in the *.env* file, *e.g.*

.. code-block:: bash

  # if HOST_DEV_DB_DATA_DIR=./db_data_dev
  # in the docker/ directory
  mkdir db_data_dev

Build the images
^^^^^^^^^^^^^^^^

.. code-block:: bash

  cd docker/db_container
  ./build.sh

Starting and stopping the database container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The database container must be started under the *docker* directory:

.. code-block:: bash

  # or docker compose
  podman-compose -f docker-compose-db-only.yml up -d

And to stop:

.. code-block:: bash

  # or docker compose
  podman-compose -f docker-compose-db-only.yml down


Backup and restore
------------------

The setup described above supplies two scripts:

- **./scripts/pre_backup.sh:** Dumps the database to the ``HOST_BACKUP_DIR``. Run it before doing a file-level backup, *e.g.* as "pre" script of your backup solution.
- **./scripts/post_restore.sh:** Load the database from ``HOST_BACKUP_DIR``. Run it just after you restored that folder from a suitable backup.

Troubleshooting
---------------

Manual database connection
^^^^^^^^^^^^^^^^^^^^^^^^^^

To directly connect to the database:

.. code-block:: bash

  # or docker
  podman exec -it docker_scimodom_db_1 mariadb -u root -p scimodom


Use the password found in *secrets/mariadb-root*. Also podman-compose/docker-compose
may be used. In case of the 'db-only' DEV setup one may do this:

.. code-block:: bash

  docker podman-compose -f docker-compose-db-only.yml  exec scimodom_db_dev mariadb -u root -p scimodom
