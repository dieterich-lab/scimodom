.. _database_overview:

Database
========

.. _data_model:

Data model
----------

Schema
^^^^^^

Schema V4 28.09.2023.
Alembic version ``a2107e9c03fc``.

.. code-block:: bash

    +--------------------+
    | Tables_in_scimodom |
    +--------------------+
    | alembic_version    |
    | assembly           |
    | assembly_version   |
    | association        |
    | data               |
    | dataset            |
    | method             |
    | modification       |
    | modomics           |
    | ncbi_taxa          |
    | organism           |
    | project            |
    | project_contact    |
    | project_source     |
    | selection          |
    | taxonomy           |
    | technology         |
    +--------------------+


.. code-block:: mysql

    CREATE TABLE `alembic_version` (
    `version_num` varchar(32) NOT NULL,
    PRIMARY KEY (`version_num`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `assembly` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(128) NOT NULL,
    `taxa_id` int(11) NOT NULL,
    `version` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `taxa_id` (`taxa_id`),
    CONSTRAINT `assembly_ibfk_1` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `assembly_version` (
    `version_num` varchar(12) NOT NULL,
    PRIMARY KEY (`version_num`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `association` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `dataset_id` varchar(12) NOT NULL,
    `selection_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `dataset_id` (`dataset_id`,`selection_id`),
    KEY `selection_id` (`selection_id`),
    CONSTRAINT `association_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`),
    CONSTRAINT `association_ibfk_2` FOREIGN KEY (`selection_id`) REFERENCES `selection` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `data` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `dataset_id` varchar(12) NOT NULL,
    `chrom` varchar(128) NOT NULL,
    `start` int(11) NOT NULL,
    `end` int(11) NOT NULL,
    `name` varchar(32) NOT NULL,
    `score` int(11) NOT NULL,
    `strand` varchar(1) NOT NULL,
    `thick_start` int(11) NOT NULL,
    `thick_end` int(11) NOT NULL,
    `item_rgb` varchar(128) NOT NULL,
    `coverage` int(11) NOT NULL,
    `frequency` int(11) NOT NULL,
    `ref_base` varchar(1) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `dataset_id` (`dataset_id`),
    CONSTRAINT `data_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `dataset` (
    `id` varchar(12) NOT NULL,
    `project_id` varchar(8) NOT NULL,
    `title` varchar(255) NOT NULL,
    `file_format` varchar(32) NOT NULL,
    `modification_type` varchar(32) NOT NULL,
    `taxa_id` int(11) NOT NULL,
    `assembly_id` int(11) NOT NULL,
    `lifted` tinyint(1) NOT NULL,
    `annotation_source` varchar(128) NOT NULL,
    `annotation_version` varchar(128) NOT NULL,
    `sequencing_platform` varchar(255) DEFAULT NULL,
    `basecalling` text DEFAULT NULL,
    `bioinformatics_workflow` text DEFAULT NULL,
    `experiment` text DEFAULT NULL,
    `external_source` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `taxa_id` (`taxa_id`),
    KEY `assembly_id` (`assembly_id`),
    KEY `dataset_ibfk_1` (`project_id`),
    CONSTRAINT `dataset_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
    CONSTRAINT `dataset_ibfk_2` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`),
    CONSTRAINT `dataset_ibfk_3` FOREIGN KEY (`assembly_id`) REFERENCES `assembly` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `method` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `cls` varchar(32) NOT NULL,
    `meth` varchar(128) NOT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `modification` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `rna` varchar(32) NOT NULL,
    `modomics_id` varchar(128) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `modomics_id` (`modomics_id`),
    CONSTRAINT `modification_ibfk_1` FOREIGN KEY (`modomics_id`) REFERENCES `modomics` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `modomics` (
    `id` varchar(128) NOT NULL,
    `name` varchar(255) NOT NULL,
    `short_name` varchar(32) NOT NULL,
    `moiety` varchar(32) NOT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `ncbi_taxa` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(128) NOT NULL,
    `taxonomy_id` int(11) NOT NULL,
    `short_name` varchar(128) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `taxonomy_id` (`taxonomy_id`),
    CONSTRAINT `ncbi_taxa_ibfk_1` FOREIGN KEY (`taxonomy_id`) REFERENCES `taxonomy` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=10091 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `organism` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `cto` varchar(255) NOT NULL,
    `taxa_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `taxa_id` (`taxa_id`),
    CONSTRAINT `organism_ibfk_1` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `project` (
    `id` varchar(8) NOT NULL,
    `title` varchar(255) NOT NULL,
    `summary` text NOT NULL,
    `date_published` datetime NOT NULL,
    `date_added` datetime NOT NULL,
    `contact_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `contact_id` (`contact_id`),
    CONSTRAINT `project_ibfk_1` FOREIGN KEY (`contact_id`) REFERENCES `project_contact` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `project_contact` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `contact_name` varchar(128) NOT NULL,
    `contact_institution` varchar(255) NOT NULL,
    `contact_email` varchar(320) NOT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `project_source` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `project_id` varchar(8) NOT NULL,
    `doi` varchar(255) DEFAULT NULL,
    `pmid` int(11) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `project_source_ibfk_1` (`project_id`),
    CONSTRAINT `project_source_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `selection` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `modification_id` int(11) NOT NULL,
    `technology_id` int(11) NOT NULL,
    `organism_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `modification_id` (`modification_id`,`technology_id`,`organism_id`),
    KEY `technology_id` (`technology_id`),
    KEY `organism_id` (`organism_id`),
    CONSTRAINT `selection_ibfk_1` FOREIGN KEY (`modification_id`) REFERENCES `modification` (`id`),
    CONSTRAINT `selection_ibfk_2` FOREIGN KEY (`technology_id`) REFERENCES `technology` (`id`),
    CONSTRAINT `selection_ibfk_3` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `taxonomy` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `domain` varchar(32) NOT NULL,
    `kingdom` varchar(32) DEFAULT NULL,
    `phylum` varchar(32) DEFAULT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `technology` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `tech` varchar(255) NOT NULL,
    `method_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `method_id` (`method_id`),
    CONSTRAINT `technology_ibfk_1` FOREIGN KEY (`method_id`) REFERENCES `method` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


Model description
^^^^^^^^^^^^^^^^^

SMID/project creation is handled by maintainers *e.g.* via request. This is currently only available via maintenance scripts (TODO via API).
A standard template is required:

.. code-block:: json

    {
        "title": "Title",
        "summary": "Summary",
        "contact_name": "Name",
        "contact_institution": "Institution",
        "contact_email": "Email",
        "date_published": "YYYY-MM-DD",
        "external_sources": {
            "doi": "doi",
            "pmid": "pmid"
        },
        "metadata": [
            {
                "rna": "mRNA",
                "modomics_id": "6A",
                "tech": "m6A-SAC-seq",
                "method_id": 8,
                "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly": "GRCh38"}
            },
            {
                "rna": "mRNA",
                "modomics_id": "6A",
                "tech": "m6A-SAC-seq",
                "method_id": 8,
                "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly": "GRCh38"}
            }
        ]
    }

``"external_sources": null`` is allowed, ``"doi": null`` or ``"pmid": null`` are allowed, but not both simultaneously. ``"external_sources"`` can be a list of entries, or a single entry (as above). ``"metadata"`` can be a list of entries (as above), or a single entry (at least one entry is required, and all keys are required). Each ``"metadata"`` entry corresponds to a given dataset (bedRMod files to be uploaded, EUFID) that will be associated with the project, *i.e.* a given SMID can have one or more dataset or EUFID. But a given dataset may also require two or more entries for ``metadata``, *e.g.* if two or more modifications are given in the same bedRMod file.

Once a SMID is created, the necessary fields are set (modifications, incl. RNA type, technology/method, organism, incl. cell/tissue/organ, and assembly), and data upload is enabled via the FE (TODO), via the API (TODO), or via maintenance scripts. At upload, these fields are selected to match a given bedRMod file, and should thus be consistent with the information from the bedRMod header.

.. attention::

    We cannot validate all fields from the header, *i.e.* compare if selected fields match those from the header, because not all information is recorded in the bedRMod format specs, the information may not be standardized, or the information may not always be easily recoverable. Currently only ``organism`` and ``assembly`` are checked. ``organism`` (``taxa_id``) is easy to validate, but ``assembly`` is not. In **Sci-ModoM**, we define a standardized assembly nomenclature (via SMID/project creation, as defined above), but the ``assembly`` from the bedRMod header is "free". Modifications selected at upload are loosely checked against those present in the bedRMod file (column 4). ``external_source`` is never checked against project sources. Handling of these cases is not yet fixed (TODO).


Nomenclature
""""""""""""

The nomenclature for modifications (table ``modomics``), technologies (table ``method``), taxa (tables ``taxonomy`` and ``ncbi_taxa``), and assemblies (table ``assembly``) is fixed. Entries in these tables allow to define options for data upload, search and compare filters.

The classification of detection technologies is taken from this [paper](https://www.nature.com/articles/s12276-022-00821-0), *.e.g.* NGS 2nd generation is subclassified into direct sequencing, chemical-assisted sequencing (m6A-SAC-seq, RiboMeth-seq, ...), Antibody-based (m6A-seq/MeRIP, ...), enzyme/protein-assisted (DART-seq, MAZTER-seq, ...).

Dates should be formatted by the following format: YYYY-MM-DD (ISO 8601).


Assembly
^^^^^^^^

Available assemblies for different organisms are grouped into an ``assembly_version``, which defines the assemblies used in **Sci-ModoM**. This version is recorded in a table of the same name. Assemblies are *tagged* by version numbers, in case more than one is available per organism. The current ``assembly_version`` prevails.

How does it work?

* When a new project is added, assembly information is required. If the assembly is already available, nothing is done. If not, a new assembly is added, with a random version number (unused, unless the assembly is a new assembly, in which case this may be part of a next version, but in general this should not happen because project creation is handled by maintainers, *e.g.* if this happens, a version upgrade may be performed beforehand).
* When data is added to a project, assembly is selected, and if this assembly does not match the current ``assembly_version``, then a liftover is performed. The dataset is marked as lifted, but the assembly version remains the one given at upload (presumably matching that from the bedRMod header), for reference.
* ``assembly_version`` can be *auto-generated* for maintenance (liftover selected datasets *e.g.* human, but not mouse; upgrade version number; tag assemblies with new version, incl. those that were not lifted but that are still valid, *i.e.* mouse)


Annotation
^^^^^^^^^^

How to handle annotations? *e.g.* a given dataset has ``annotation_source`` and ``annotation_version`` (not standardized).
How important it is to "stick" to that? Can we have *e.g.* a given Ensembl annotation/version for a given organism, and use this?
With the current model, we only need annotations to classify the data into regions, and assign gene names.
How do we do this? We could use Ensembl tables, add genomic information at upload, to avoid performing operations in queries, ... ?


Download
^^^^^^^^

The data can be download back to bedRMod format, but it is unclear how to handle header information when *e.g.* query results include records from different studies, incl. different organisms/assemblies/annotations, *etc.*.

If downloading a single dataset *e.g.* corresponding to one original bedRMod file, the data is converted back to bedRMod format. The header is re-written using standad nomenclature if available. If the data is marked as lifted, the lifted data is written to file (we do not keep the orginal data), but a note is added to the header. The rationale is the following: data downloaded from the DB is that from the DB, and not that from the publication, *etc.*. If the DB is usign a certain assembly version, the the data downloaded will be of that assembly.


.. _data_setup:

Setup
-----

At lauchtime, the app uses tables defined in ``config.py`` to perform an ``INSERT... ON DUPLICATE KEY UPDATE``

.. code-block:: python

    setup = SetupService(app.session)
    setup.upsert_all()

These tables (``modomics``, ``method``, ``taxonomy``, ``ncbi_taxa``, ``assembly``, and ``assembly_version``) allow to define base options for project creation, and establish a standard terminology for the application. The import format is *CSV*, and the header must match the column names (including *id*) from the corresponding database table, *e.g. ncbi_taxa.csv*

.. code-block:: bash

    id,name,short_name,taxonomy_id
    9606,Homo sapiens,H. sapiens,1
    10090,Mus musculus,M. musculus,1

*Note:* These tables should only change with database version. We can skip the upsert at production.

For any given database, the upsert can also be done for one table at a time, or all tables (via ``config.py``), without launching the app

.. code-block:: bash

    upsert -db DATABASE [--model MODEL] [--table TABLE] [--all]


Projects are added (currently only without launching the app) with

.. code-block:: bash

    add-project -db DATABASE -p PROJECT

where PROJECT is a (path to a) json file, as described above.


After project creation, dataset can be added (currently only without launching the app) with

.. code-block:: bash

    add-dataset -db DATABASE -smid PROJECT_ID --title TITLE --file FILE [-o ORGANISM] [-a ASSEMBLY] [-m MODIFICATION [MODIFICATION ...]]
    [-rna {mRNA,rRNA,tRNA} [{mRNA,rRNA,tRNA} ...]] [-t TECHNOLOGY] [-cto CELL_TYPE] [--assembly-id ASSEMBLY_ID]
    [--modification-id MODIFICATION_ID [MODIFICATION_ID ...]] [--technology-id TECHNOLOGY_ID] [--cto-id CTO_ID]

where FILE is a valid bedRMod file.


Local setup
^^^^^^^^^^^

We use ``python-dotenv`` to manage local environment variables. As of 20.09.2023, if ``LOCAL_APP`` is set, ``config.py`` uses ``.env.local``, else ``.env.development``. The former is a database that we re-create as needed, while the latter is the standard development database.

.. code-block:: mysql

    -- sudo mysql
    -- DROP DATABASE scimodom_local;
    CREATE DATABASE IF NOT EXISTS scimodom_local;
    GRANT ALL PRIVILEGES ON scimodom_local.* TO 'eboileau'@'localhost';


Versioning
^^^^^^^^^^

We use Alembic

.. code-block:: bash

    alembic revision --autogenerate [-m "message"]
    alembic upgrade head
