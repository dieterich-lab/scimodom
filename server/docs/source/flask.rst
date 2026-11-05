.. _flask:

Flask CLI
=========

How to initialize or update the database and manage projects and data.

Most commands ask for confirmation. Use ``--yes`` to skip and ``--traceback`` to show the full traceback of an error.

.. _data_setup:

Initialization
--------------

Data import
^^^^^^^^^^^

The command ``flask setup upsert [FILE_NAME]...`` performs an ``INSERT... ON DUPLICATE KEY UPDATE`` using a list of files defined in ``SetupService``:

.. code-block:: python

    FILE_NAME_TO_DB_TABLE_MAP = {
        "rna_type.csv": RNAType,
        "modomics.csv": Modomics,
        "taxonomy.csv": Taxonomy,
        "ncbi_taxa.csv": Taxa,
        "assembly.csv": Assembly,
        "assembly_version.csv": AssemblyVersion,
        "annotation.csv": Annotation,
        "annotation_version.csv": AnnotationVersion,
        "method.csv": DetectionMethod,
    }


These files allow to define base options for project creation, and establish a standard terminology for the application. They must exist and be located under ``IMPORT_PATH`` (development) or ``HOST_IMPORT_DIR`` (production). By default, this path is located under *server/import*, and can be specified in the environment file. The import format is *CSV*, and the header must match the column names (including *id*) from the corresponding database table.

For example:

* *ncbi_taxa.csv* with column names taken from the corresponding declarative model *Taxa*

.. code-block:: bash

    id,name,short_name,taxonomy_id
    9606,Homo sapiens,H. sapiens,8128e900
    10090,Mus musculus,M. musculus,8128e900

* *assembly.csv* with column names taken from the corresponding declarative model *Assembly*

.. code-block:: bash

    id,name,alt_name,taxa_id,version
    1,GRCh38,hg38,9606,K9FeTPiZ4abQ
    2,GRCm39,mm39,10090,K9FeTPiZ4abQ

* *annotation.csv* with column names taken from the corresponding declarative model *Annotation*

.. code-block:: bash

    id,release,taxa_id,source,version
    1,110,9606,ensembl,cp6qKL4t4Wws
    2,110,10090,ensembl,cp6qKL4t4Wws

where *version* for assembly and annotation must match the current version specified in *assembly_version.csv* and *annotation_version.csv*, respectively.

The models are defined in `scimodom.database.models <https://github.com/dieterich-lab/scimodom/blob/master/server/src/scimodom/database/models.py>`_.

.. important::

   The command is idempotent, and must be run after the database schema was created or upgraded, and whenever the files change. The app does not do this when it starts: this is done in the production container before the server is started, and must be called in development.


Assembly and annotation
^^^^^^^^^^^^^^^^^^^^^^^

The steps above only allow to define assemblies and annotations in the database, but do not create the required data files. To create assembly
and annotation files, use


.. code-block:: bash

    flask assembly add [OPTIONS] ASSEMBLY_ID


.. code-block:: bash

    flask annotation add [OPTIONS] --source [ensembl|gtrnadb] TAXA_ID


For example, to create the human assembly and annotation data files


.. code-block:: bash

    flask assembly add 1
    flask annotation --source ensembl 9606

where ``ASSEMBLY_ID=1`` matches the assembly ID from *Assembly* corresponding to the current human assembly version, as initially specified in *assembly.csv*, and where ``TAXA_ID=9606`` matches the value from *Taxa*, as initially specified in *ncbi_taxa.csv*.

Data is written to ``DATA_PATH`` (development) or ``HOST_DATA_DIR`` (production).


.. _project_data_setup:

Project and data management
---------------------------

Projects-related sub-commands are called using the ``project`` command.

To add a new selection

.. code-block:: bash

    flask selection add [OPTIONS] --rna-type TEXT --modification TEXT --taxid INTEGER --cto TEXT --method TEXT --technology TEXT

To added a project

.. code-block:: bash

    flask project add [OPTIONS] REQUEST_UUID

To add a user to the project use the option ``--add-user``. The email address given in the template associated with the ``REQUEST_UUID`` must match a valid user. After project creation, a dataset can be added with

.. code-block:: bash

    flask dataset add [OPTIONS] --assembly-id INTEGER --rna-type TEXT --modification-ids INTEGER --organism-id INTEGER --technology-id INTEGER SMID TITLE FILENAME

Dataset upload is normally done via POST request upon login to the running application, accessible through *User menu* > *Data* > *Dataset upload*.

These steps, *i.e.* project creation and dataset upload, can be done all at once with

.. code-block:: bash

    flask dataset batch [OPTIONS] --rna-type TEXT REQUEST_UUID INPUT_DIRECTORY

The ``note`` from the standard project metadata template must contain the dataset file name and title as follows: ``file=filename.bedrmod, title=title``. All bedRMod files must be under ``INPUT_DIRECTORY``. The request and all files are validated first (use ``--dry-run`` to only validate), and nothing is written if there is a problem. Datasets are then imported one by one: a dataset that fails is skipped, the command exits with an error, and the dataset can be added afterwards with ``flask dataset add``.

To facilitate batch upload, project templates can be created from a tabulated list of datasets with

.. code-block:: bash

    flask project create-template [OPTIONS] --title TEXT --summary TEXT --surname TEXT --forename TEXT --institution TEXT --email TEXT DATASET_CSV

For a detailed description of DATASET_CSV format, use the ``--help`` flag, *e.g.* ``flask project create-template --help``.

Permissions can be updated with

.. code-block:: bash

    flask project add-user [OPTIONS] USERNAME SMID

If required, a project and all associated data can be removed with

.. code-block:: bash

    flask project delete [OPTIONS] SMID

Datasets are deleted one by one, and the project last. If the command fails part way, what was deleted stays deleted, and it can be run again to resume with the remaining datasets.

To force update the charts, run

.. code-block:: bash

    flask charts sunburst-update [OPTIONS]


Audit trail
^^^^^^^^^^^

Commands that add or remove datasets, projects and selections (``dataset add``, ``dataset batch``, ``project add``, ``project add-user``, ``project delete``, ``selection add``) write two records to the logger ``scimodom.audit``: *started* (before any confirmation), and *finished* with the outcome (*success*, *aborted* if the confirmation was refused, *interrupted*, or *failed* with the error). A record contains the time (UTC), the OS user, the command and its arguments, *e.g.*

.. code-block:: text

    2026-11-04T06:09:04Z [AUDIT] event=project.delete phase=started user=app uid=1000 command="flask project delete" params={"smid": "12345678", "traceback": false, "yes": true}

Records are written to *stderr*. For a persistent trail, set ``AUDIT_LOG_FILE`` in the environment file to a file path: only audit records are written to this file (appended; opened when the first record is written, and reopened if the file is rotated). Other logging is not affected. If the file cannot be written, a warning is shown on *stderr*, and the command is not affected (the records are still written to *stderr*).

In the production container, ``AUDIT_LOG_FILE`` is ``/logs/audit.log``, and the directory is mounted from ``HOST_LOG_DIR``. The file is created at container start, owned by the application user, and is also used by commands run with ``docker exec``.
