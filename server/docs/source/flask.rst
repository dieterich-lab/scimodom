.. _flask:

Flask CLI
=========

Flask CLI documentation.

.. _data_setup:

Setup
-----

At lauchtime, the app uses tables defined in ``config.py`` to perform an ``INSERT... ON DUPLICATE KEY UPDATE``

.. code-block:: python

    setup_service = get_setup_service()
    setup_service.upsert_all()

These tables (``rna_type``, ``modomics``, ``method``, ``taxonomy``, ``ncbi_taxa``, ``assembly``, ``assembly_version``, ``annotation``, and ``annotation_version``) allow to define base options for project creation, and establish a standard terminology for the application. The import format is *CSV*, and the header must match the column names (including *id*) from the corresponding database table, *e.g. ncbi_taxa.csv*

.. code-block:: bash

    id,name,short_name,taxonomy_id
    9606,Homo sapiens,H. sapiens,8128e900
    10090,Mus musculus,M. musculus,8128e900

The upsert can be done for one model/table at a time, or forced with

.. code-block:: bash

    flask setup [OPTIONS]

For OPTIONS, use the ``--help`` flag, *e.g.* ``flask setup --help``.

To manage assemblies or annotations, use


.. code-block:: bash

    flask assembly [OPTIONS]


.. code-block:: bash

    flask annotation [OPTIONS] --source [ensembl|gtrnadb] TAXID


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

Permissions can be updated with

.. code-block:: bash

    flask permission [OPTIONS] USERNAME SMID
