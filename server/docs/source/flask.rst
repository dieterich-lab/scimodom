.. _flask:

Flask CLI
=========

Flask CLI documentation.

.. _data_setup:

Setup
-----

Data import
^^^^^^^^^^^

At launch time, the app performs an ``INSERT... ON DUPLICATE KEY UPDATE`` using a list of files defined in ``SetupService``:


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


These files (``rna_type.csv``, ``modomics.csv``, ``taxonomy.csv``, ``ncbi_taxa.csv``, ``assembly.csv``, ``assembly_version.csv``, ``annotation.csv``, ``annotation_version.csv``, and ``method.csv``) allow to define base options for project creation, and establish a standard terminology for the application. They must exist and be located under ``IMPORT_PATH`` (development) or ``HOST_IMPORT_DIR`` (production). By default, this path is located under *server/import*, and can be specified in the environment file. The import format is *CSV*, and the header must match the column names (including *id*) from the corresponding database table.

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

The models are defined in `scimodom.database.models <https://github.com/dieterich-lab/scimodom/blob/7d4dad0f69c5c7d9988d5dcc9c51eba4ddfdc61b/server/src/scimodom/database/models.py>`_.

The upsert can be done for one model/table at a time, or forced with

.. code-block:: bash

    flask setup [OPTIONS]

For OPTIONS, use the ``--help`` flag, *e.g.* ``flask setup --help``.


Assembly and annotation
^^^^^^^^^^^^^^^^^^^^^^^

The steps above only allow to define assemblies and annotations in the database, but do not create the required data files. To create assembly
and annotation files, use


.. code-block:: bash

    flask assembly [OPTIONS]


.. code-block:: bash

    flask annotation [OPTIONS] --source [ensembl|gtrnadb] TAXID


For example, to create the human assembly and annotation data files


.. code-block:: bash

    flask assembly --id 1
    flask annotation --source ensembl 9606

where ``--id 1`` matches the assembly ID from *Assembly* corresponding to the current human assembly version, as initially specified in *assembly.csv*, and where Taxa ID ``9606`` matches the value from *Taxa*, as initially specified in *ncbi_taxa.csv*.

Data is written to ``DATA_PATH`` (development) or ``HOST_DATA_DIR`` (production).


.. _project_data_setup:

Project and data management
---------------------------

Projects are added with

.. code-block:: bash

    flask project [OPTIONS] REQUEST_UUID

A user is automatically associated with a project upon creation using the email address given in the template associated with the ``REQUEST_UUID``.
After project creation, dataset can be added with

.. code-block:: bash

    flask dataset [OPTIONS] --assembly INTEGER --annotation [ensembl|gtrnadb] --modification INTEGER --organism INTEGER --technology INTEGER FILENAME SMID TITLE

Dataset upload is normally done via POST request upon login to the running application, accessible through *User menu* > *Data* > *Dataset upload*.
These steps, except user-project association, can be done all at once with

.. code-block:: bash

    flask batch [OPTIONS] --annotation [ensembl|gtrnadb] INPUT_DIRECTORY [REQUEST_UUIDS]...

The ``note`` from the standard project metadata template must contain the dataset file name and title as follows: ``file=filename.bedrmod, title=title``. All bedRMod files must be under ``INPUT_DIRECTORY``.

To facilitate batch upload, project templates can be created from a tabulated list of datasets with

.. code-block:: bash

    flask metadata [OPTIONS] --title TEXT --summary TEXT --surname TEXT --forename TEXT --institution TEXT --email TEXT DATASET_CSV

For a detailed description of DATASET_CSV format, use the ``--help`` flag, *e.g.* ``flask metadata --help``.

A new selection can be added with

.. code-block:: bash

    flask selection [OPTIONS] --rna TEXT --modification TEXT --taxid INTEGER --cto TEXT --method-id TEXT --technology TEXT

Permissions can be updated with

.. code-block:: bash

    flask permission [OPTIONS] USERNAME SMID

If required, a project and all associated data can be removed with

.. code-block:: bash

    flask delete [OPTIONS] SMID

To force update the charts, run

.. code-block:: bash

    flask sunburst-update [OPTIONS]
