.. _database_overview:

Database
========

Data model
----------

Description and workflow
^^^^^^^^^^^^^^^^^^^^^^^^

To create a project request, go to *User menu* > *Data* > *Project template*. Upon successful submission, a draft template is
created and an email is sent to the system administrator. In the background, the following standard template is created:

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

Each project is assigned a **Sci-ModoM** identifier or **SMID**. The actual project creation and user-project association is currently only handled by ``flask`` commands, see `Flask CLI <https://dieterich-lab.github.io/scimodom/flask.html>`_. Once a project is created, you are associated with the newly created
project, and you can see it under *User menu* > *Settings*. You are then allowed to upload dataset (bedRMod) and to attach BAM files to a dataset.
This is done using the upload forms (*Upload bedRMod*, *Attach BAM files*) under *User menu* > *Data* > *Dataset upload*.
Upon successful upload, a dataset is assigned a EUF identifier or **EUFID**. A given project (**SMID**) can thus have one or more dataset (**EUFID**) attached to it.

Once created, projects are immediately made public. On upload, dataset are immediately made public. Projects and dataset cannot be changed or deleted, *i.e.* **SMID** and **EUFID** arfe permanent identifiers. You can however decide to upload and/or remove dataset attachments (BAM files).


.. attention::

    A given dataset or bedRMod file can contain more than one modification, as reported in column 4 (MODOMICS short name), but this should
    be for the same RNA type. A dataset or bedRMod file can only contain ONE RNA type, ONE technology, ONE organism (incl. cell type, tissue,
    or organ), and records from the same assembly. The best way to handle treatment and/or conditions is to have as many bedRMod
    files as required to describe the experimental protocol, and provide a meaningful title for each file.

.. attention::

    The terminology for RNA types is built around the concept of sequencing method rather than the biological definition of RNA species. **Sci-ModoM**
    currently supports the following types: *(i)* RNAs obtained from *WTS* or *whole transcriptome sequencing* and *(ii)* *tRNA* or *transfer RNA* (*to be soon available*). If you use a general sequencing method and your data contains *mRNAs* and *non-coding RNAs* (mostly long, but also short such as *mt-RNAs*,
    residual *rRNAs*, *etc.*), then choose *WTS*.

.. attention::

    Dataset upload will fail if there are too many skipped records *e.g.* due to inconsistent format specifications. The threshold is set at 5%, *i.e.*
    up to 5% of your records can be discarded silently before upload fails. This allows *e.g.* to upload dataset where a small number of entries
    are from contigs or scaffolds, *etc.*

    Dataset that are of a different assembly version are lifted over before being written to the database. Typically, a number of features may
    not be "mappable". Since contigs/scaffolds are discarded, and the data has been validated for organism, assembly, *etc.*, the number
    of ummaped features should be small. The threshold is currently set a 30%, *i.e.* up to 30% of your records are allowed to de discarded
    silently before upload fails.


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

Finally, upon successful upload and annotation, the gene cache is updated. This cache consist of sets of gene symbols (``GenomicAnnotation.name``)
coming from ``DataAnnotation`` for all dataset associated with a given *selection* (RNA modification, organism, and technology). These gene sets are
used to feed the gene selection ``AutoComplete`` in the Search View.


.. note::

   ``GenomicAnnotation`` has eventually unused column ``annotation_id``, since only ONE annotation is actually allowed for the
   current database ``annotation_version``. Would using partitions make sense?



Database upgrade
""""""""""""""""

It is currently not possible to perform a full database upgrade. A method implementation should do the following:

* Update ``Annotation``, ``AnnotationVersion``.
* Call ``AnnotationService.create_annotation``, but before we clean ``DataAnnotation`` and ``GenomicAnnotation`` as explained above. Here
  we don't delete ``Data``, but just re-annotate records.


.. _data_model:
