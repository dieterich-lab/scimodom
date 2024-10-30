.. _database_overview:

Data model and design
=====================

Nomenclature
------------

The nomenclature for RNA types (table ``rna_type``), modifications (table ``modomics``), technologies (table ``method``), and taxa (tables ``taxonomy`` and ``ncbi_taxa``) is fixed. Assembly and annotation follow the Ensembl format specification.

The classification of detection technologies is taken from this `paper <https://www.nature.com/articles/s12276-022-00821-0>`_ *.e.g.* NGS 2nd generation is subclassified into direct sequencing, chemical-assisted sequencing (m6A-SAC-seq, RiboMeth-seq, ...), Antibody-based (m6A-seq/MeRIP, ...), enzyme/protein-assisted (DART-seq, MAZTER-seq, ...).

Dates are formatted as: YYYY-MM-DD (ISO 8601).

Data management
---------------

This section presents a general explanation how projects are created and how datasets are associated with projects. It is assumed
that the application is already up and running, see `Flask CLI Setup <https://dieterich-lab.github.io/scimodom/flask.html#setup>`_.

Consult the `Data Management <https://scimodom.dieterichlab.org/documentation/management>`_ section of the Documentation for examples.

Project creation
^^^^^^^^^^^^^^^^

To create a project request, go to *User menu* > *Data* > *Project template*. Upon successful submission, a draft template is
created. The project is not immediately available; the request template must first be reviewed by the system administrator.

.. admonition:: For maintainers

   Project templates can be created from a CSV file using the CLI command ``flask metadata``. The actual project creation and
   user-project association are also handled by ``flask`` commands, see `Flask CLI Project and data management <https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management>`_ for details.

Each project is assigned a **Sci-ModoM** identifier or **SMID**. This identifier is permanent. Once a project is created, you are associated
with the newly created project, and you can see it under *User menu* > *Settings*. You are then allowed to upload dataset (bedRMod) and to attach BAM files to a dataset.

Project template
""""""""""""""""

In the background, the following standard template is created:

.. code-block:: json

    {
        "title": "Project Title",
        "summary": "Project Summary",
        "contact_name": "Surname, Forename",
        "contact_institution": "Institution",
        "contact_email": "email@example.com",
        "date_published": "2024-06-11T00:00:00",
        "external_sources": [
            {
                "doi": "10.XXXX/...",
                "pmid": null
            }
        ],
        "metadata": [
            {
                "rna": "WTS",
                "modomics_id": "2000000006A",
                "tech": "m6A-SAC-seq",
                "method_id": "e00d694d",
                "organism": {"taxa_id": 9606, "cto": "HeLa", "assembly_name": "GRCh38", "assembly_id": 1},
                "note": "Note"
            },
            {
                "rna": "WTS",
                "modomics_id": "2000000006A",
                "tech": "m6A-SAC-seq",
                "method_id": "e00d694d",
                "organism": {"taxa_id": 9606, "cto": "HEK293", "assembly_name": "GRCh38", "assembly_id": null},
                "note": ""
            }
        ]
    }

``"external_sources": []`` and ``"date_published": null`` are allowed (no public sources). If there is at least one source, one of DOI or PMID must be defined, *i.e.* they cannot be both ``"doi": null`` and ``"pmid": null``. DOI format includes only the prefix and suffix, without the doi.org proxy server. ``"metadata"`` is a list of entries with at least one entry. All keys are required, ``"assembly_id"`` and ``"note"`` are optional. Each ``"metadata"`` entry provides information for a given dataset (bedRMod file). A single dataset may also require two or more entries for ``metadata`` *e.g.* if two or more modifications are given in the same bedRMod file.


Dataset upload
^^^^^^^^^^^^^^

This is done using the upload forms (*Upload bedRMod*, *Attach BAM files*) under *User menu* > *Data* > *Dataset upload*.
Upon successful upload, a dataset is assigned a EUF identifier or **EUFID**. This identifier is permanent. A given project (**SMID**) can
have one or more dataset (**EUFID**) attached to it.

On upload, dataset are immediately made public. You cannot change or delete projects and datasets. You can however decide to upload and/or remove dataset attachments (BAM files).


.. admonition:: For maintainers

   Datasets can be added one at a time or in batch, and records can be updated for an existing dataset. Consult the
   `Flask CLI Project and data management <https://dieterich-lab.github.io/scimodom/flask.html#project-and-data-management>`_ section.


.. important::

    A given dataset or bedRMod file can contain more than one modification, as reported in column 4 (MODOMICS short name), but this should
    be for the same RNA type. A dataset or bedRMod file can only contain ONE RNA type, ONE technology, ONE organism (incl. cell type, tissue,
    or organ), and records from the same assembly. The best way to handle treatment and/or conditions is to have as many bedRMod
    files as required to describe the experimental protocol, and provide a meaningful title for each file.

.. attention::

    The terminology for RNA types is built around the concept of sequencing method rather than the biological definition of RNA species.
    **Sci-ModoM** currently only supports the following type: RNAs obtained from *WTS* or *whole transcriptome sequencing*. We plan
    to include additional types, such as *tRNA* or *transfer RNA* in a very near future. If you use a general sequencing method and your
    data contains *mRNAs* and *non-coding RNAs* (mostly long, but also short such as *mt-RNAs*, residual *rRNAs*, *etc.*), then *WTS* is
    the right RNA type.

.. caution::

    Dataset upload will fail if there are too many skipped records *e.g.* due to inconsistent or wrong data formatting. Consult the
    `bedRMod format specification <https://dieterich-lab.github.io/scimodom/bedrmod.html>`_ for details, and the
    the `Data Management (Dataset upload errors) <https://scimodom.dieterichlab.org/documentation/management>`_ section of the
    Documentation for examples.

    In practice, a threshold is set at 5%, *i.e.* up to 5% of your records can be discarded silently before upload fails. This
    allows *e.g.* to upload dataset where a small number of entries are from contigs or scaffolds, *etc.*

    Dataset that are of a different assembly version are lifted over before being written to the database. Unmapped features
    are discarded. The threshold is currently set a 30%, *i.e.* up to 30% of your records are allowed to de discarded
    silently before upload fails.

    The thresholds are defined in *scimodom.utils.specs.enums.ImportLimits*.


Assembly and annotation
-----------------------

This section presents a general explanation how assemblies and annotations are handled by the application, and how they are created.
This is currently only valid for Ensembl releases. The current release and destinations for Ensembl services are defined in an Ensembl
enumeration in `scimodom.utils.specs.enums.Ensembl <https://github.com/dieterich-lab/scimodom/blob/23e7d2bc872343517e981613d5f847a4cfa2292e/server/src/scimodom/utils/specs/enums.py>`_.

Assemblies and annotations for the current version must be available, see `Flask CLI Setup <https://dieterich-lab.github.io/scimodom/flask.html#setup>`_.

Assembly
^^^^^^^^

Available assemblies for different organisms are grouped into an ``assembly_version``, which defines the assemblies used in **Sci-ModoM** (w/o patch number/minor release). This version is recorded in a table of the same name. Assemblies are *tagged* by version numbers, in case more than one is available per organism. The current ``assembly_version`` prevails. This ``assembly_version`` is implicitely *matched* with the Ensembl enumeration.

How does it work?

* When a new project is added, assembly information is required. If the assembly is already available, nothing is done. If not, a new
  assembly is added. This has no effect on the database ``assembly_version``, but merely downloads chain files allowing to lift over
  data to the current ``assembly_version``.

* During data upload, records from contigs/scaffolds are discarded (only records from chromosomes are kept). Dataset that are not matching
  the current database ``assembly_version`` are lifted over.

.. important::

    Chromosomes must be formatted following the Ensembl short format *e.g.* 1 and not chr1, or MT and not chrM. The ``#assembly`` header
    entry from the bedRMod file must match exactly the chosen assembly from the database, and must follow the Ensembl nomenclature *e.g.*
    GRCh38 for human.

Annotation
^^^^^^^^^^

Available annotations are grouped into an ``annotation_version``, which defines the annotations used in **Sci-ModoM**. This version is recorded in a table of the same name. Annotations are *tagged* by version numbers, in case more than one is available per organism. The current ``annotation_version`` prevails, and must implicitely *match* the current ``assembly_version``, although this is not forced into the database. Currently, the Ensembl annotation service checks that the annotation release matches that from the Ensembl enumeration, but this is not done at instantiation. A given Ensembl release is valid for all organisms.

How does it work?

* Upon creation of a new annotation, features (Exon, CDS, 3'UTR, 5'UTR, introns, and intergenic regions) are extracted and written to disk. The ``genomic_annotation`` table is updated.

* During data upload, records are annotated *on the fly* to ``data_annotation``. A given modification can thus be annotated *e.g.* as Exon,
  3'UTR, and CDS, possibly with different ``gene_name`` or ``gene_id``, resulting in more than one entry in ``data_annotation``.

* Finally, upon successful upload and annotation, the gene cache is updated. This cache consist of sets of gene symbols
  (``genomic_annotation.name``) coming from ``data_annotation`` for all dataset associated with a given *selection* (RNA modification,
  organism, and technology). These gene sets are used to feed the gene selection ``AutoComplete`` in the Search View.


Database upgrade
^^^^^^^^^^^^^^^^

.. admonition:: For maintainers

  It is currently not possible to perform a database upgrade. A method implementation is described below.


* Update the Ensembl emumeration prior to running the upgrade method.
* Update ``assembly_version``, ``assembly``, ``annotation_version``, and ``annotation``, or only the latter two tables if performing
  an annotation-only upgrade.
* Update ``genomic_annotation`` and ``data_annotation``.

For an annotation-only upgrade, the assembly information (``release.json`` and ``info.json``) will change, but the data
files (``chrom.sizes``, FASTA and CHAIN files) should not. A general liftover is not necessary, but data records need to be re-annotated.
Since the PK of ``genomic_annotation`` is ``gene_id``, before calling ``create_annotation``, ``data_annotation`` must be deleted, then
the old ``annotation_id`` from ``GenomicAnnotation`` must be deleted *e.g.*

.. code-block:: mysql

    delete from data_annotation where gene_id like 'ENSMUS%';
    delete from genomic_annotation where annotation_id = 2;

For a full upgrade, assemblies and data files need to be re-created. In addition to the above, all ``data`` records have to be re-added
(lifted over and re-annotated). The "dependency" between assembly and annotation should be made explicit, and this should be better integrated
with the database model.


.. _data_model:
