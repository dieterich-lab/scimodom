# Container Setup

## Prerequisites

### Container Tools: podman-compose or docker-compose

You will need a container CLI, which can handle docker-compose-like
files, e.g. podman-compose or the original docker-compose. Docker Swarm
is very restricted and may **not** work.

If podman is correctly installed, with podman all operations can be done
as a non-root user.

### Image Building: NodeJS

In addition, NodeJS and npm are required on the machine, which builds
the container images.

## Configure .env

Create a file .env in the 'docker' folder based on env_example.
You may stick with the relative path names used there, but then you
need to make sure that all scripts are run from the docker folder.

## Build the Images

```bash
cd docker/db_container
./build.sh
cd ../app_container
./build.sh
```

## Optional: Copy to Live Instance

If the images are built on a different machine, or if multiple deployments
are run on the same container host the required data must be deployed
to that system or a separate folder per instance.

In case of an deployment to a different container host the following data
need to be transferred:

* The images, e.g. via a Docker repository
  * scimodom_db:latest
  * scimodom_app:latest
* The docker/scripts folder
* The docker-compose.yml
* Your .env file.

In case multiple instances are run on the same host, a separate folder
needs to be crated for each instance. The same data is needed as above.
Make sure that the ports, paths and names in the .env files don't collide. 

## Set up the local directories

In the folder where your keep your .env and your docker-compose.yml file
create the folder 'secrets' containing your secrets. Also, you will
have to create folders for the database and it's backups. This can be
done a follows:

```bash
./scripts/create_local_folders.sh
```

The following files are required:

* secrets/mariadb-root: Password of the root user of the MariaDB database.
* secrets/mariadb-scimodom: Password of the scimodom user of the MariaDB database.

Use just letters and digits in the passwords because they may be used
in database connect strings. Characters with special meanings in URLs
like '/', '@' or ':' may not work.  Later changes only have effect if
the database container is recreated. That will reset the database
completely. So you may have to restore a backup.

**TODO**: Populate import folder!!!

## Starting and Stopping

To start the containers just use the docker-compos.yml, e.g.:

```bash
podman-compose up -d
```

And to stop:

```bash
podman-compose down -d
```

## Backup and Restore

The setup described above supplies two scripts:

* **./scripts/pre_backup.sh:** Dumps the database to the $HOST_BACKUP_DIR as
  defined in your setup. Run it before doing a file-level backup of these folder,
  e.g. as 'pre' script of your backup solution.
* **./scripts/post_restore.sh:** Load the database from $HOST_BACKUP_DIR.
  Run it just after you restored that folder from a suitable backup.

## Troubleshooting

### Manual database connection

To directly connect use this:

```bash
podman exec -it docker_scimodom_db_1 mariadb -u root -p --database scimodom
```

Use the password found in secrets/mariadb-root.

## Development Setup

The database can be run container and connected with the application running
locally by using docker-compose-db-only.yml. If the system already runs a
different MariaDB/MySQL instance the MARIADB_DEV_PORT must be changed in
the docker/.env file. When running it the first time, you need to set up the
secrets create the data folder for the DEV database:

```bash
./scripts/create_local_folders.sh
mkdir db_data_dev
podman-compose -f docker-compose-db-only.yml up -d
```

TIn the ../server/.env the correct DATABASE_URI must be configured:

```
DATABASE_URI=mysql+mysqldb://scimodom:PASSWORD@127.0.0.1:3306/scimodom
```

Replace **PASSWORD** with the contents of your 'secrets/mariadb-scimodom' file.
In case you changed **MARIADB_DEV_PORT** you may have to change the port after
**127.0.0.1**. Now the database schema can be initialized with alembic:

```bash
cd ../server
alembic upgrade head
```
