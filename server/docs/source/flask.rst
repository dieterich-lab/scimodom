.. _flask:

Flask CLI
=========

.. admonition:: For maintainers

  How to initialize or update the database and manage projects and data. Most commands ask for confirmation; use ``--yes`` to skip and ``--traceback`` to show the full traceback of an error.

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
        "annotation_release.csv": AnnotationRelease,
        "annotation.csv": Annotation,
        "annotation_version.csv": AnnotationVersion,
        "method.csv": DetectionMethod,
    }

.. important::

   The order is load-bearing: a table must come after the tables it references. *annotation.csv* references both
   *assembly.csv* and *annotation_release.csv*.


These files provide seed data to populate the database, establishing a standard terminology for the application. They must exist and be located under ``IMPORT_PATH`` (development) or ``HOST_IMPORT_DIR`` (production). By default, this path is located under *server/import*, and can be specified in the environment file. The import format is *CSV*, and the header must match the column names (including *id*) from each of the corresponding database table.

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

* *annotation_release.csv* with column names taken from the corresponding declarative model *AnnotationRelease*

.. code-block:: bash

    source,release,archive
    ensembl,110,jul2023

The *archive* may be left empty for a provider that serves no per-release archive, so that there is no release-specific
page to link to. It is not part of the key, so this does not affect the constraint that an annotation can only exist for
a release declared here.

* *annotation.csv* with column names taken from the corresponding declarative model *Annotation*

.. code-block:: bash

    id,release,assembly_id,source,version
    1,110,1,ensembl,cp6qKL4t4Wws
    2,110,2,ensembl,cp6qKL4t4Wws

where *version* for assembly and annotation must match the current version specified in *assembly_version.csv* and *annotation_version.csv*, respectively.

An annotation references the assembly it is in the coordinate system of, not a taxa: the taxa is reached through the
assembly. The *assembly_id* of an annotation must be an assembly of the current assembly version. The *(source, release)*
of an annotation must have a row in *annotation_release.csv*, which records where that provider serves that release;
Ensembl publishes the mapping of a release onto its archive as an HTML list only, so it cannot be derived.

The models are defined in `scimodom.database.models <https://github.com/dieterich-lab/scimodom/blob/master/server/src/scimodom/database/models.py>`_.

.. important::

   The command is idempotent, and must be run after the database schema was created or upgraded, and whenever the files change. The app does not do this on startup: this is done in the production container before the server is started, and must be called before starting the development server.


Assembly and annotation
^^^^^^^^^^^^^^^^^^^^^^^

The steps above only allow to define assemblies and annotations in the database, but do not create the required data files. To create assembly
and annotation files, use


.. code-block:: bash

    flask assembly add [OPTIONS] TAXA_ID


.. code-block:: bash

    flask annotation add [OPTIONS] --source [ensembl|gtrnadb] TAXA_ID


For example, to create the human assembly and annotation data files


.. code-block:: bash

    flask assembly add --release 110 --archive jul2023 9606
    flask annotation --source ensembl 9606

where ``TAXA_ID=9606`` matches the value from *Taxa*, as initially specified in *ncbi_taxa.csv*. Exactly one assembly of an organism matches the current version; there is no way to provision an assembly that is not the current one.

Data is written to ``DATA_PATH`` (development) or ``HOST_DATA_DIR`` (production).

Nothing is inferred from the code: which snapshot to install is stated once, when it is installed. The release is validated
against the archive before anything is downloaded, and both are recorded in the assembly manifest (``manifest.json``),
together with the assembly information reported by the REST API. Everything that needs to know which snapshot is installed
reads it from there, so it stays true after an upgrade changes what is current.

.. note::

    ``manifest.json`` supersedes ``info.json`` and ``release.json``. For an installation created before it existed, write it
    from the files already on the system with

    .. code-block:: bash

        flask assembly migrate-manifest [OPTIONS] TAXA_ID

    Nothing is downloaded and the current assembly is not touched. The release and archive are recorded as given, so they must
    match the files actually installed. The legacy files are left in place and can be removed once the application has been
    verified against the manifest.


.. _project_data_setup:

Project and data management
---------------------------

Projects-related sub-commands are called using the ``project`` command.

To add a project

.. code-block:: bash

    flask project add [OPTIONS] REQUEST_UUID

To add a user to the project use the option ``--add-user``. The email address given in the template associated with the ``REQUEST_UUID`` must match a valid user. The metadata entries of the template define the project selections, *i.e.* the combinations of modification, organism, and technology for which datasets can be added to this project. A dataset (``dataset add``, ``dataset batch``, or upload via the web interface) is rejected if its combination is not a selection of its project.

.. note::
  The corresponding selection, which makes the data available for search, is automatically created when the first dataset is added, and removed with the last dataset. The table ``project_selection`` has no foreign key to ``selection``, so the two keep their separate life cycles.

To add a selection to an existing project

.. code-block:: bash

    flask project add-selection [OPTIONS] --rna-type TEXT --modification TEXT --taxid INTEGER --cto TEXT --method TEXT --technology TEXT SMID

After project creation, a dataset can be added with

.. code-block:: bash

    flask dataset add [OPTIONS] --assembly-id INTEGER --rna-type TEXT --modification-ids INTEGER --organism-id INTEGER --technology-id INTEGER SMID TITLE FILENAME

Dataset upload is normally done via POST request upon login to the running application, accessible through *User menu* > *Data* > *Dataset upload*.

These steps, *i.e.* project creation and dataset upload, can be done all at once with

.. code-block:: bash

    flask dataset batch [OPTIONS] REQUEST_UUID INPUT_DIRECTORY

The ``note`` from the standard project metadata template must contain the dataset file name and title as follows: ``file=filename.bedrmod, title=title``. All bedRMod files must be under ``INPUT_DIRECTORY``. The RNA type of a dataset is taken from the template, and must be the same for all its modifications. The request and all files are validated first (use ``--dry-run`` to only validate), and nothing is written if there is a problem. Datasets are then imported one by one: a dataset that fails is skipped, the command exits with an error, and the dataset can be added afterwards with ``flask dataset add``.

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

Cached data for the main page (the *index*: the data for the sunburst charts, and the aggregates, *i.e.* the number of records and sites per taxon and modification) is updated in the background after datasets or projects have been added or removed. To force an update, run

.. code-block:: bash

    flask cache update [OPTIONS]

or only ``flask cache update-sunburst`` or ``flask cache update-aggregates``. The cached files are stored in ``cache/index`` (``sunburst_search.json``, ``sunburst_browse.json``, ``modification_aggregates.json``) and are replaced atomically, so that requests are served from the previous version until the update is complete. Only one update of each kind runs at a time, an update requested while another is running is run once the running update has finished. This cache is never generated within a request (it can take longer than a request is allowed to run): until it has been generated for the first time (*e.g.* after an upgrade, as it replaces ``cache/sunburst``, which is no longer used and can be removed), the affected endpoints respond with *503* (*Service Unavailable*, with a *Retry-After* header), and request the update of this cache. The page has to be reloaded once the update is complete. To avoid this, run ``flask cache update`` after the upgrade.


Audit trail
^^^^^^^^^^^

Commands that add or remove datasets, projects and project selections (``dataset add``, ``dataset batch``, ``project add``, ``project add-user``, ``project add-selection``, ``project delete``) write two records to the logger ``scimodom.audit``: *started* (before any confirmation), and *finished* with the outcome (*success*, *aborted* if the confirmation was refused, *interrupted*, or *failed* with the error). A record contains the time (UTC), the OS user, the command and its arguments, *e.g.*

.. code-block:: text

    2026-11-04T06:09:04Z [AUDIT] event=project.delete phase=started user=app uid=1000 command="flask project delete" params={"smid": "12345678", "traceback": false, "yes": true}

Records are written to *stderr*. For a persistent trail, set ``AUDIT_LOG_FILE`` in the environment file to a file path: only audit records are written to this file (appended; opened when the first record is written, and reopened if the file is rotated). Other logging is not affected. If the file cannot be written, a warning is shown on *stderr*, and the command is not affected (the records are still written to *stderr*).

In the production container, ``AUDIT_LOG_FILE`` is ``/logs/audit.log``, and the directory is mounted from ``HOST_LOG_DIR``. The file is created at container startup, owned by the application user, and is also used by commands run with ``docker exec``.
