.. _database_overview:

Database
========

Data model
----------

Model description
^^^^^^^^^^^^^^^^^

Project creation is handled via request. Each project is assigned a **Sci-ModoM** identifier or SMID. The request form is accessible upon login to **Sci-ModoM** and must be completed online. In the background, the following standard template is created:

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
                "modomics_id": "2000000006A",
                "tech": "m6A-SAC-seq",
                "method_id": "e00d694d",
                "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly": "GRCh38"}
            },
            {
                "rna": "mRNA",
                "modomics_id": "2000000006A",
                "tech": "m6A-SAC-seq",
                "method_id": "e00d694d",
                "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly": "GRCh38"}
            }
        ]
    }

``"external_sources": null`` is allowed, ``"doi": null`` or ``"pmid": null`` are allowed, but not both simultaneously. ``"external_sources"`` can be a list of entries, or a single entry (as above). ``"date_published": null`` is allowed (no public sources). ``"metadata"`` can be a list of entries (as above), or a single entry (at least one entry is required, and all keys are required). Each ``"metadata"`` entry provides information for a given dataset (bedRMod file). Upon successful upload, a dataset is assigned a EUF identifier or EUFID. A given project (SMID) can thus have one or more dataset (EUFID) attached to it. A single dataset may also require two or more entries for ``metadata`` *e.g.* if two or more modifications are given in the same bedRMod file.

.. attention::

   A given dataset or bedRMod file can contain more than one modification, as reported in column 4 (MODOMICS short name), but this should
   be for the same RNA type. A dataset or bedRMod file can only contain ONE RNA type, ONE technology, ONE organism (incl. cell type, tissue,
   or organ), and records from the same assembly. The best way to handle treatment and/or conditions is to have as many bedRMod
   files as required to describe the experimental protocol, and provide a meaningful title for each file.

Workflow
""""""""

Upon successful project request submission, a draft template is created and an email is sent to the system administrator. A project is created and
a user is associated with the newly created project. The actual project creation and user-project association is currently only handled
by ``flask`` commands, see `_data_setup`_. Once a project is created, a user is allowed to upload dataset (bedRMod) and to attach BAM files to a dataset.
This is handled by the user using the upload forms (Upload bedRMod, Attach BAM files).

A number of validation routines are implemented to ensure that the uploaded dataset is conform to bedRMod specifications, that the dataset metadata
is consistent with the chosen project selection, *etc.* Dataset that are of a different assembly version are lifted over before being written to
the database. Finally, dataset are annotated and the gene cache is updated.


Nomenclature
""""""""""""

The nomenclature for RNA types (table ``rna_type``), modifications (table ``modomics``), technologies (table ``method``), and taxa (tables ``taxonomy`` and ``ncbi_taxa``) is fixed. Assembly and annotation follow the Ensembl format.

The classification of detection technologies is taken from this `paper <https://www.nature.com/articles/s12276-022-00821-0>`_ *.e.g.* NGS 2nd generation is subclassified into direct sequencing, chemical-assisted sequencing (m6A-SAC-seq, RiboMeth-seq, ...), Antibody-based (m6A-seq/MeRIP, ...), enzyme/protein-assisted (DART-seq, MAZTER-seq, ...).

Dates are formatted as: YYYY-MM-DD (ISO 8601).


Assembly
^^^^^^^^

Available assemblies for different organisms are grouped into an ``assembly_version``, which defines the assemblies used in **Sci-ModoM** (w/o patch number/minor release). This version is recorded in a table of the same name. Assemblies are *tagged* by version numbers, in case more than one is available per organism. The current ``assembly_version`` prevails.

How does it work?

* When a new project is added, assembly information is required. If the assembly is already available, nothing is done. If not, a new
  assembly is added. This has no effect on the database ``assembly_version``, but merely downloads chain files allowing to lift over
  data to the current ``assembly_version``.

* During data upload, records from contigs/scaffolds are discarded (only records from chromosomes are kept). Dataset that are not matching
  the current database ``assembly_version`` are lifted over.

.. attention::

   Chromosomes must be formatted following the Ensembl short format *e.g.* 1 and not chr1, or MT and not chrM. The ``#assembly`` header
   entry from the bedRMod file must match exactly the chosen assembly from the database, and must follow the Ensembl nomenclature *e.g.*
   GRCh38 for human.

Database upgrade
""""""""""""""""

It is currently not possible to perform a full database upgrade. A method implementation should do the following:

* Update ``AssemblyVersion``, ``Assembly``, ``AnnotationVersion``, and ``Annotation``.
* For "untouched" ``taxid``, upsert database version in place, so that the ids remain unchanged.
* For changed assemblies/annotations, create new ids, then call ``AssemblyService.create_new`` and ``AnnotationService.create_annotation``.
* Since the PK of ``GenomicAnnotation`` is ``gene_id``, before calling ``create_annotation``, ``DataAnnotation`` must be deleted, then the
  "old" ``annotation_id`` from ``GenomicAnnotation`` *e.g.*

.. code-block:: mysql

    delete from data_annotation where gene_id like 'ENSMUS%';
    delete from genomic_annotation where annotation_id = 2;

* For all affected dataset, delete ``Data``, liftover all records, re-insert new ``Data``, then re-annotate records to ``DataAnnotation``
  using newly updated ``GenomicAnnotation``.


Annotation
^^^^^^^^^^

Available annotations are grouped into an ``annotation_version``, which defines the annotations used in **Sci-ModoM**. This version is recorded in a table of the same name. Annotations are *tagged* by version numbers, in case more than one is available per organism. The current ``annotation_version`` prevails, and must "implicitely" match the current ``assembly_version``, although this is not forced into the database.

Upon creation of a new annotation, files are written to disk, and to ``GenomicAnnotation`` (gene_id, annotation_id, gene_name, gene_biotype).
During dataset upload, records are annotated "on the fly" to ``DataAnnotation`` (gene_id, data_id, feature). Features are Exon, CDS, 3'UTR, 5'UTR, introns, and intergenic regions. They are obtained using bedtools intersections. Feature sets are first merged on ``gene_name``, ``annotation_id``, ``strand``, ``gene_id``, and ``gene_biotype``. All intersections are strand-aware, except for the intergenic region. Introns are obtained by subtracting exons from genomic features. Intergenic regions are the chromosome complement of genomic regions.

A given modification can thus be annotated *e.g.* as Exon, 3'UTR, and CDS, possibly with different ``gene_name`` or ``gene_id``, resulting in more than one entry in ``DataAnnotation``. This has the advantage of allowing a fine-grain annotation.

.. note::

   ``GenomicAnnotation`` has eventually unused column ``annotation_id``, since only ONE annotation is actually allowed for the
   current database ``annotation_version``. Would using partitions make sense?


Database upgrade
""""""""""""""""

It is currently not possible to perform a full database upgrade. A method implementation should do the following:

* Update ``Annotation``, ``AnnotationVersion``.
* Call ``AnnotationService.create_annotation``, but before we clean ``DataAnnotation`` and ``GenomicAnnotation`` as explained above. Here
  we don't delete ``Data``, but just re-annotate records.


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

Projects are added with

.. code-block:: bash

    flask project [OPTIONS] TEMPLATE

A user is automatically associated with a project upon creation using the email address given in the ``TEMPLATE``.
After project creation, dataset can be added with

.. code-block:: bash

    flask dataset [OPTIONS] SMID TITLE FILENAME

Dataset upload is normally done via POST request upon login to the running application, accessible through User menu > Data > Dataset upload.
These steps, except user-project association, can be done all at once with

.. code-block:: bash

    flask batch DIRECTORY [TEMPLATES]

Permissions can be updated with

.. code-block:: bash

    flask permission USERNAME SMID

To manage assemblies or annotations, use

.. code-block:: bash

    flask annotation [OPTIONS] ID

.. code-block:: bash

    flask assembly [OPTIONS]

For OPTIONS, use the ``--help`` flag, *e.g.* ``flask assembly --help``.


.. _data_model:


Schema
^^^^^^

Schema 05.2024.
Alembic version ``ac1b984c4751``.

.. code-block:: bash

    +--------------------------+
    | Tables_in_scimodom       |
    +--------------------------+
    | alembic_version          |
    | annotation               |
    | annotation_version       |
    | assembly                 |
    | assembly_version         |
    | association              |
    | bam_file                 |
    | data                     |
    | data_annotation          |
    | dataset                  |
    | genomic_annotation       |
    | method                   |
    | modification             |
    | modomics                 |
    | ncbi_taxa                |
    | organism                 |
    | project                  |
    | project_contact          |
    | project_source           |
    | rna_type                 |
    | selection                |
    | taxonomy                 |
    | technology               |
    | user                     |
    | user_project_association |
    +--------------------------+

.. code-block:: mysql

    DROP TABLE IF EXISTS `alembic_version`;
    CREATE TABLE `alembic_version` (
    `version_num` varchar(32) NOT NULL,
    PRIMARY KEY (`version_num`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `annotation`;
    CREATE TABLE `annotation` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `release` int(11) NOT NULL,
    `taxa_id` int(11) NOT NULL,
    `version` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_annotation_rtv` (`release`,`taxa_id`,`version`),
    KEY `ix_annotation_taxa_id` (`taxa_id`),
    CONSTRAINT `fk_annotation_taxa_id_ncbi_taxa` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `annotation_version`;
    CREATE TABLE `annotation_version` (
    `version_num` varchar(12) NOT NULL,
    PRIMARY KEY (`version_num`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `assembly`;
    CREATE TABLE `assembly` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(128) NOT NULL,
    `taxa_id` int(11) NOT NULL,
    `version` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_assembly_ntv` (`name`,`taxa_id`,`version`),
    UNIQUE KEY `uq_assembly_name` (`name`),
    KEY `ix_assembly_taxa_id` (`taxa_id`),
    CONSTRAINT `fk_assembly_taxa_id_ncbi_taxa` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `assembly_version`;
    CREATE TABLE `assembly_version` (
    `version_num` varchar(12) NOT NULL,
    PRIMARY KEY (`version_num`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `association`;
    CREATE TABLE `association` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `selection_id` int(11) NOT NULL,
    `dataset_id` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_assoc` (`selection_id`,`dataset_id`),
    KEY `ix_association_dataset_id` (`dataset_id`),
    KEY `ix_association_selection_id` (`selection_id`),
    CONSTRAINT `fk_association_dataset_id_dataset` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`),
    CONSTRAINT `fk_association_selection_id_selection` FOREIGN KEY (`selection_id`) REFERENCES `selection` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=128 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `bam_file`;
    CREATE TABLE `bam_file` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `original_file_name` varchar(1024) NOT NULL,
    `storage_file_name` varchar(256) NOT NULL,
    `dataset_id` varchar(12) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_bam_file_storage_file_name` (`storage_file_name`),
    KEY `ix_bam_file_dataset_id` (`dataset_id`),
    CONSTRAINT `fk_bam_file_dataset_id_dataset` FOREIGN KEY (`dataset_id`) REFERENCES `dataset` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `data`;
    CREATE TABLE `data` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `association_id` int(11) NOT NULL,
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
    KEY `idx_data_sort` (`chrom`,`start`,`end`),
    KEY `ix_data_association_id` (`association_id`),
    KEY `ix_data_coverage` (`coverage`),
    KEY `ix_data_frequency` (`frequency`),
    KEY `ix_data_score` (`score`),
    CONSTRAINT `fk_data_association_id_association` FOREIGN KEY (`association_id`) REFERENCES `association` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=3492749 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `data_annotation`;
    CREATE TABLE `data_annotation` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `data_id` int(11) NOT NULL,
    `gene_id` varchar(128) NOT NULL,
    `feature` varchar(32) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_data_annotation_data_id` (`data_id`,`gene_id`,`feature`),
    KEY `ix_data_annotation_data_id` (`data_id`),
    KEY `ix_data_annotation_feature` (`feature`),
    KEY `ix_data_annotation_gene_id` (`gene_id`),
    CONSTRAINT `fk_data_annotation_data_id_data` FOREIGN KEY (`data_id`) REFERENCES `data` (`id`),
    CONSTRAINT `fk_data_annotation_gene_id_genomic_annotation` FOREIGN KEY (`gene_id`) REFERENCES `genomic_annotation` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=6749262 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `dataset`;
    CREATE TABLE `dataset` (
    `id` varchar(12) NOT NULL,
    `project_id` varchar(8) NOT NULL,
    `title` varchar(255) NOT NULL,
    `modification_type` varchar(32) NOT NULL,
    `sequencing_platform` varchar(255) DEFAULT NULL,
    `basecalling` text DEFAULT NULL,
    `bioinformatics_workflow` text DEFAULT NULL,
    `experiment` text DEFAULT NULL,
    `external_source` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_dataset_project_id` (`project_id`),
    CONSTRAINT `fk_dataset_project_id_project` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `genomic_annotation`;
    CREATE TABLE `genomic_annotation` (
    `id` varchar(128) NOT NULL,
    `annotation_id` int(11) NOT NULL,
    `name` varchar(128) DEFAULT NULL,
    `biotype` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_genomic` (`annotation_id`,`biotype`,`name`),
    KEY `ix_genomic_annotation_annotation_id` (`annotation_id`),
    CONSTRAINT `fk_genomic_annotation_annotation_id_annotation` FOREIGN KEY (`annotation_id`) REFERENCES `annotation` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `method`;
    CREATE TABLE `method` (
    `id` varchar(8) NOT NULL,
    `cls` varchar(32) NOT NULL,
    `meth` varchar(128) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_method_meth` (`meth`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `modification`;
    CREATE TABLE `modification` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `modomics_id` varchar(128) NOT NULL,
    `rna` varchar(32) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_modification_modomics_id` (`modomics_id`,`rna`),
    KEY `ix_modification_modomics_id` (`modomics_id`),
    KEY `fk_modification_rna_rna_type` (`rna`),
    CONSTRAINT `fk_modification_modomics_id_modomics` FOREIGN KEY (`modomics_id`) REFERENCES `modomics` (`id`),
    CONSTRAINT `fk_modification_rna_rna_type` FOREIGN KEY (`rna`) REFERENCES `rna_type` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `modomics`;
    CREATE TABLE `modomics` (
    `id` varchar(128) NOT NULL,
    `name` varchar(255) NOT NULL,
    `short_name` varchar(32) NOT NULL,
    `moiety` varchar(32) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_modomics_name` (`name`),
    UNIQUE KEY `uq_modomics_short_name` (`short_name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `ncbi_taxa`;
    CREATE TABLE `ncbi_taxa` (
    `id` int(11) NOT NULL,
    `name` varchar(128) NOT NULL,
    `short_name` varchar(128) NOT NULL,
    `taxonomy_id` varchar(8) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ncbi_taxa_name` (`name`),
    UNIQUE KEY `uq_ncbi_taxa_short_name` (`short_name`),
    KEY `ix_ncbi_taxa_taxonomy_id` (`taxonomy_id`),
    CONSTRAINT `fk_ncbi_taxa_taxonomy_id_taxonomy` FOREIGN KEY (`taxonomy_id`) REFERENCES `taxonomy` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `organism`;
    CREATE TABLE `organism` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `taxa_id` int(11) NOT NULL,
    `cto` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_organism_taxa_id` (`taxa_id`,`cto`),
    KEY `ix_organism_cto` (`cto`),
    KEY `ix_organism_taxa_id` (`taxa_id`),
    CONSTRAINT `fk_organism_taxa_id_ncbi_taxa` FOREIGN KEY (`taxa_id`) REFERENCES `ncbi_taxa` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `project`;
    CREATE TABLE `project` (
    `id` varchar(8) NOT NULL,
    `title` varchar(255) NOT NULL,
    `summary` text NOT NULL,
    `contact_id` int(11) NOT NULL,
    `date_published` datetime DEFAULT NULL,
    `date_added` datetime NOT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_project_contact_id` (`contact_id`),
    CONSTRAINT `fk_project_contact_id_project_contact` FOREIGN KEY (`contact_id`) REFERENCES `project_contact` (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `project_contact`;
    CREATE TABLE `project_contact` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `contact_name` varchar(128) NOT NULL,
    `contact_institution` varchar(255) NOT NULL,
    `contact_email` varchar(320) NOT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `project_source`;
    CREATE TABLE `project_source` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `project_id` varchar(8) NOT NULL,
    `doi` varchar(255) DEFAULT NULL,
    `pmid` int(11) DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_project_source_project_id` (`project_id`),
    CONSTRAINT `fk_project_source_project_id_project` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `rna_type`;
    CREATE TABLE `rna_type` (
    `id` varchar(32) NOT NULL,
    `name` varchar(128) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_rna_type_name` (`name`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `selection`;
    CREATE TABLE `selection` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `modification_id` int(11) NOT NULL,
    `organism_id` int(11) NOT NULL,
    `technology_id` int(11) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `idx_select` (`modification_id`,`organism_id`,`technology_id`),
    KEY `ix_selection_modification_id` (`modification_id`),
    KEY `ix_selection_organism_id` (`organism_id`),
    KEY `ix_selection_technology_id` (`technology_id`),
    CONSTRAINT `fk_selection_modification_id_modification` FOREIGN KEY (`modification_id`) REFERENCES `modification` (`id`),
    CONSTRAINT `fk_selection_organism_id_organism` FOREIGN KEY (`organism_id`) REFERENCES `organism` (`id`),
    CONSTRAINT `fk_selection_technology_id_technology` FOREIGN KEY (`technology_id`) REFERENCES `technology` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `taxonomy`;
    CREATE TABLE `taxonomy` (
    `id` varchar(8) NOT NULL,
    `domain` varchar(32) NOT NULL,
    `kingdom` varchar(32) DEFAULT NULL,
    `phylum` varchar(32) DEFAULT NULL,
    PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `technology`;
    CREATE TABLE `technology` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `method_id` varchar(8) NOT NULL,
    `tech` varchar(255) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_technology_method_id` (`method_id`,`tech`),
    KEY `ix_technology_method_id` (`method_id`),
    KEY `ix_technology_tech` (`tech`),
    CONSTRAINT `fk_technology_method_id_method` FOREIGN KEY (`method_id`) REFERENCES `method` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `user`;
    CREATE TABLE `user` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `email` varchar(320) NOT NULL,
    `state` enum('wait_for_confirmation','active') NOT NULL,
    `password_hash` varchar(128) DEFAULT NULL,
    `confirmation_token` varchar(32) DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `ix_user_email` (`email`)
    ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

    DROP TABLE IF EXISTS `user_project_association`;
    CREATE TABLE `user_project_association` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user_id` int(11) NOT NULL,
    `project_id` varchar(8) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_user_project_association_project_id` (`project_id`),
    KEY `ix_user_project_association_user_id` (`user_id`),
    CONSTRAINT `fk_user_project_association_project_id_project` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
    CONSTRAINT `fk_user_project_association_user_id_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
