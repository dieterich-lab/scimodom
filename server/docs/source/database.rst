.. _database_overview:

Database
========

.. _data_model:

Data model
----------

Schema
^^^^^^

Schema 01.2024.
Alembic version ``79fa0c30513f``.

.. code-block:: bash

    +--------------------+
    | Tables_in_scimodom |
    +--------------------+
    | alembic_version    |
    | annotation         |
    | annotation_version |
    | assembly           |
    | assembly_version   |
    | association        |
    | data               |
    | dataset            |
    | genomic_annotation |
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

    CREATE TABLE `annotation` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `release` int(11) NOT NULL,
        `taxa_id` int(11) NOT NULL,
        `version` varchar(12) NOT NULL,
        PRIMARY KEY (`id`),
        KEY `taxa_id` (`taxa_id`),
        CONSTRAINT `annotation_ibfk_1` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `annotation_version` (
        `version_num` varchar(12) NOT NULL,
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
        PRIMARY KEY (`id`),
        KEY `dataset_id` (`dataset_id`),
        CONSTRAINT `data_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=48935 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `dataset` (
        `id` varchar(12) NOT NULL,
        `project_id` varchar(8) NOT NULL,
        `title` varchar(255) NOT NULL,
        `file_format` varchar(32) NOT NULL,
        `modification_type` varchar(32) NOT NULL,
        `taxa_id` int(11) NOT NULL,
        `assembly_id` int(11) NOT NULL,
        `lifted` tinyint(1) NOT NULL,
        `annotation_source` varchar(128) DEFAULT NULL,
        `annotation_version` varchar(128) DEFAULT NULL,
        `sequencing_platform` varchar(255) DEFAULT NULL,
        `basecalling` text DEFAULT NULL,
        `bioinformatics_workflow` text DEFAULT NULL,
        `experiment` text DEFAULT NULL,
        `external_source` varchar(255) DEFAULT NULL,
        PRIMARY KEY (`id`),
        KEY `project_id` (`project_id`),
        KEY `taxa_id` (`taxa_id`),
        KEY `assembly_id` (`assembly_id`),
        CONSTRAINT `dataset_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
        CONSTRAINT `dataset_ibfk_2` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`),
        CONSTRAINT `dataset_ibfk_3` FOREIGN KEY (`assembly_id`) REFERENCES `assembly` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    CREATE TABLE `genomic_annotation` (
        `id` int(11) NOT NULL AUTO_INCREMENT,
        `annotation_id` int(11) NOT NULL,
        `gene_name` varchar(128) DEFAULT NULL,
        `gene_id` varchar(128) DEFAULT NULL,
        `gene_biotype` varchar(255) DEFAULT NULL,
        `data_id` int(11) NOT NULL,
        `feature` varchar(32) NOT NULL,
        PRIMARY KEY (`id`),
        KEY `annotation_id` (`annotation_id`),
        KEY `data_id` (`data_id`),
        CONSTRAINT `genomic_annotation_ibfk_1` FOREIGN KEY (`annotation_id`) REFERENCES `annotation` (`id`),
        CONSTRAINT `genomic_annotation_ibfk_2` FOREIGN KEY (`data_id`) REFERENCES `data` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=37296 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

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

SMID/project creation is handled by maintainers *e.g.* via request. This is currently only available via maintenance scripts.
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

The classification of detection technologies is taken from this `paper <https://www.nature.com/articles/s12276-022-00821-0>`_ *.e.g.* NGS 2nd generation is subclassified into direct sequencing, chemical-assisted sequencing (m6A-SAC-seq, RiboMeth-seq, ...), Antibody-based (m6A-seq/MeRIP, ...), enzyme/protein-assisted (DART-seq, MAZTER-seq, ...).

Dates should be formatted by the following format: YYYY-MM-DD (ISO 8601).


Assembly
^^^^^^^^

Available assemblies for different organisms are grouped into an ``assembly_version``, which defines the assemblies used in **Sci-ModoM** (w/o patch number/minor release). This version is recorded in a table of the same name. Assemblies are *tagged* by version numbers, in case more than one is available per organism. The current ``assembly_version`` prevails.

How does it work?

* When a new project is added, assembly information is required. If the assembly is already available, nothing is done. If not, a new assembly is added. If this assembly is a newer version, a database version upgrade may be required.

* During data upload:
    * records from contigs/scaffolds, *etc.* are discarded (only records from chromosomes are kept);
    * assembly is selected, and if this assembly does not match the current ``assembly_version``, then a liftover is performed (Dataset marked as lifted);
    * currently, the Dataset ``assembly_id`` is the one given at upload (presumably matching that from the bedRMod header).

* ``assembly_version`` can be *auto-generated* for maintenance (liftover selected datasets *e.g.* human, but not mouse; upgrade version number; tag assemblies with new version, incl. those that were not lifted but that are still valid, *i.e.* mouse)


Annotation
^^^^^^^^^^

To annotate a dataset, all of its records are intersected in turn with features such as Exon, CDS, 3'UTR, 5'UTR, introns, and intergenic regions. This is currently done at dataset upload. Feature sets are first merged on ``gene_name``, ``annotation_id``, ``strand``, ``gene_id``, and ``gene_biotype``. All intersections are strand-aware, except for the intergenic region. Introns are obtained by subtracting exons from genomic features. Intergenic regions are the chromosome complement of genomic regions. This is used to fill ``GenomicAnnotation``.

A given modification can thus be annotated *e.g.* as Exon, 3'UTR, and CDS, possibly with different ``gene_name`` or ``gene_id``, resulting in more than one entry in ``GenomicAnnotation``. This has the advantage of allowing a fine-grain annotation. But when a given intersection results in more than one ``gene_name``, ``gene_id``, and/or ``gene_biotype``, the corresponding field is left empty (NULL). These are merged during query, resulting in *e.g.*

.. code-block:: bash

    15	90984058	90984059	Y	150	-	372	15	PRC1	ENSG00000198901,ENSG00000284946	protein_coding	3\'UTR,CDS,Exon



Download
^^^^^^^^

The data can be download back to bedRMod format, but it is unclear how to handle header information when *e.g.* query results include records from different studies, incl. different organisms/assemblies/annotations, *etc.*.

If downloading a single dataset *e.g.* corresponding to one original bedRMod file, the data is converted back to bedRMod format. The header is re-written using standad nomenclature if available. If the data is marked as lifted, the lifted data is written to file (we do not keep the orginal data), but a note is added to the header. The rationale is the following: data downloaded from the DB is that from the DB, and not that from the publication, *etc.*. If the DB is usign a certain assembly version, the the data downloaded will be of that assembly.


.. _data_setup:

Setup
-----

*All this is subject to change*

At lauchtime, the app uses tables defined in ``config.py`` to perform an ``INSERT... ON DUPLICATE KEY UPDATE``

.. code-block:: python

    setup = SetupService(app.session)
    setup.upsert_all()

These tables (``modomics``, ``method``, ``taxonomy``, ``ncbi_taxa``, ``assembly``, and ``assembly_version``) allow to define base options for project creation, and establish a standard terminology for the application. The import format is *CSV*, and the header must match the column names (including *id*) from the corresponding database table, *e.g. ncbi_taxa.csv*

.. code-block:: bash

    id,name,short_name,taxonomy_id
    9606,Homo sapiens,H. sapiens,1
    10090,Mus musculus,M. musculus,1

This is typically done *e.g.*

.. code-block:: bash

    # under docker
    docker compose -f docker-compose-db-only.yml up -d
    # under server
    alembic upgrade head
    upsert --all # <- this is subject to change!


Projects are added with

.. code-block:: bash

    add-project -p PROJECT

where PROJECT is a (path to a) json file, as described above.

After project creation, dataset can be added with

.. code-block:: bash

    add-dataset -smid PROJECT_ID --title TITLE --file FILE [-o ORGANISM] [-a ASSEMBLY] [-m MODIFICATION [MODIFICATION ...]]
    [--modomics] [-rna {mRNA,rRNA,tRNA} [{mRNA,rRNA,tRNA} ...]] [-t TECHNOLOGY] [-cto CELL_TYPE] [--assembly-id ASSEMBLY_ID]
    [--modification-id MODIFICATION_ID [MODIFICATION_ID ...]] [--technology-id TECHNOLOGY_ID] [--cto-id CTO_ID]

where FILE is a valid bedRMod file.

These steps can be done all at once with

.. code-block:: bash

    add-all -d DIR -pt PROJECT

where DIR is a directory with project templates and dataset files, and PROJECT is the name of a project (w/o extension).
