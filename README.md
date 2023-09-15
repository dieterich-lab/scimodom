# Sci-ModoM

The prototype running at [sci-modom](https://scimodom.dieterichlab.org/) is built on the
web front-end for the doRiNA database.

## Migration

- Phased out/not actively maintained front-end technologies (KnockoutJS).
- API not tailored to our aims.
- Operations performed on files (no database).
- Missing functionalities (authentication, _etc._).

Proposed architecture: single-page application (SPA) to separate Flask and VueJS.

### Back-end (server)

- Python3 and Flask
- MySQL database
- Redis cache

- Model:
  - API
  - Services (operate on data objects)
  - Data Objects (stateful models, CRUD)
  - Data Store Drivers (intermediary interface between application and datastore)

### Front-end (client)

- VueJS
- vue-router
- pinia (state management)
- Firebase (authentication)

- Model:
  - SPA

## Installation

During migration, `scimodom` remains locally installable:

```bash
git clone https://github.com/dieterich-lab/scimodom
cd scimodom
pip install [-e] .
```

Also make sure to have a Redis server running.

## Running the Web UI

To run the development / test server:

```bash
redis-server & rqworker --path path/to/scimodom/scimodom/server/src/scimodom &
python app.py &
```

## License

`scimodom` is licensed under the GNU Affero General Public Licence (AGPL) version 3.
See `LICENSE` file for details.
