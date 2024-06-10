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


To manage assemblies or annotations, use

.. code-block:: bash

    flask annotation [OPTIONS] ID

.. code-block:: bash

    flask assembly [OPTIONS]

For OPTIONS, use the ``--help`` flag, *e.g.* ``flask assembly --help``.

.. _project_data_setup:

Project and data management
---------------------------

Projects are added with

.. code-block:: bash

    flask project [OPTIONS] TEMPLATE

A user is automatically associated with a project upon creation using the email address given in the ``TEMPLATE``.
After project creation, dataset can be added with

.. code-block:: bash

    flask dataset [OPTIONS] SMID TITLE FILENAME

Dataset upload is normally done via POST request upon login to the running application, accessible through *User menu* > *Data* > *Dataset upload*.
These steps, except user-project association, can be done all at once with

.. code-block:: bash

    flask batch DIRECTORY [TEMPLATES]

This requires a non-standard project template (json) with additional keys: ``file_name`` and ``data_title`` for each ``metadata`` value, *e.g.*

.. code-block:: json

    {
        ...
        "metadata": {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "m6A-SAC-seq",
            "method_id": "e00d694d",
            "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly": "GRCh38"},
            "file_name": "filename.bedrmod",
            "data_title": "HeLa WT treatment A replicate 1",
            "extra": [
                "Homo sapiens",
                "HeLa",
                "wild type",
                "treatment A",
                "polyA RNA"
            ]
        }
    }

Additional keys are ignored and can be used for documentation. All templates and bedRMod files must be under the same directory.
Values in the template are used *as is* to query and update the database.

Permissions can be updated with

.. code-block:: bash

    flask permission USERNAME SMID
