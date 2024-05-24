# Container Setup

## Prerequisites

### Container tools: podman-compose or docker-compose

You need a container CLI to handle docker-compose-like files _e.g._ podman-compose or the original docker-compose.
Docker Swarm is very restricted and may **not** work. The following versions are known to work:

- podman 4.3.1 with podman-compose 1.0.3 on Debian 12
- docker 20.10 with docker-compose 1.25.0 on Debian 11

If podman is correctly installed, with podman all operations can be done as a non-root user.

### Image building: Node.js

In addition, Node.js and npm are required on the machine, which builds the container images. Vue.js presently requires Node.js 16 or newer.
The following version is known to work:

- Node.js 18.13.0 on Debian 12
- Node.js 18.17.1 on Debian 11 from nodesource.com

## Configure .env_docker

Create a file _.env_docker_ in the _docker_ directory based on [env_docker_example](env_docker_example).
You may stick with the relative path names used there, but then you need to make sure that all scripts are run from the _docker_ directory.

## Build the images

```bash
# check https://hub.docker.com/_/mariadb for reference
cd docker/db_container
./build.sh
cd ../app_container
./build.sh
```

## Optional: copy to live instance

If the images are built on a different machine, or if multiple deployments are run on the same container host, the required data must be deployed
to that system or a separate folder per instance.

In case of a deployment to a different container host the following data need to be transferred:

- The images, _e.g._ via a Docker repository
  - The database image, e.g. scimodom_db:latest
  - The application image, e.g. scimodom_app:latest
- The docker/scripts folder
- The docker-compose.yml
- Your .env file - see below.

In case multiple instances are run on the same host, a separate folder needs to be created for each instance. The same data is needed as above.
Make sure that the ports, paths and names in the _.env_ files don't collide!

## Set up your .env file

Create a file .env in the same folder as the docker-compose.yml you use.
An example may be found here: [../server/env_example](env_example).

## Set up the local directories

In the folder where your keep your _.env_ and your _docker-compose.yml_ file create the folder _secrets_ containing your secrets. Also, you will
have to create folders for the database and it's backups. This can be done a follows:

```bash
./scripts/create_local_folders.sh
```

The following files are required:

- secrets/mariadb-root: Password of the root user of the MariaDB database.
- secrets/mariadb-scimodom: Password of the scimodom user of the MariaDB database.

Use just letters and digits in the passwords because they may be used in database connect strings. Characters with special meanings in URLs
like '/', '@' or ':' may not work. Later changes only have effect if the database container is recreated. That will reset the database
completely. So you may have to restore from backup.

## Starting and stopping

To start the containers just use the _docker-compose.yml_:

```bash
podman-compose up -d
```

And to stop:

```bash
podman-compose down -d
```

## Backup and restore

The setup described above supplies two scripts:

- **./scripts/pre_backup.sh:** Dumps the database to the $HOST*BACKUP_DIR as
  defined in your setup. Run it before doing a file-level backup of these folder,
  \_e.g.* as 'pre' script of your backup solution.
- **./scripts/post_restore.sh:** Load the database from $HOST_BACKUP_DIR.
  Run it just after you restored that folder from a suitable backup.

## Troubleshooting

### Manual database connection

To directly connect use this:

```bash
podman exec -it docker_scimodom_db_1 mariadb -u root -p --database scimodom
```

Use the password found in secrets/mariadb-root.

## Development Setup

The database can be run using a container and connected with the application running locally by using
_docker-compose-db-only.yml_. To do so, you first need a separate _docker/.env_ file. It may be as short
as this:

```bash
DB_IMAGE_NAME=scimodom_db:latest
MARIADB_DEV_PORT=3307
HOST_BACKUP_DIR=backup
HOST_SECRETS_DIR=secrets
HOST_DEV_DB_DATA_DIR=db_data_dev
```

Please note, that the example above use the non-standard port 3307 to avoid clashes with a local MariaDB/Mysql
installation.

```bash
./scripts/create_local_folders.sh
mkdir db_data_dev
podman-compose -f docker-compose-db-only.yml up -d
```

Now you can set up _server/.env_:

- Start with server/env_example.
- Change _DATABASE_URI_ to match your setup, especially:
- The port must match _MARIADB_DEV_PORT_ from docker/.env
- The password is one you find in the file _docker/secrets/mariadb-scimodom_.

The resulting line should look like this:

```
DATABASE_URI=mysql+mysqldb://scimodom:YourPassword@127.0.0.1:3307/scimodom
```

Now the database schema can be initialized with alembic:

```bash
cd ../server
alembic upgrade head
```
