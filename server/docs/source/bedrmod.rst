.. _euf:

The bedRMod format
==================

The go-to resource and primary reference is the official `EU format specifications <https://dieterich-lab.github.io/euf-specs/>`_.
Users should always refer to the latest version.

.. attention::

   Sci-ModoM enforces stricter requirements for data upload. This documentation introduces these requirements.


Prerequisites for data upload
-----------------------------

.. hint::

  A bedRMod file always contains data lines for one organism, one assembly and annotation, and one RNA type. For data upload,
  a dataset or bedRMod file should, in addition, only contain data lines for one detection technology. For example, if a bedRMod file
  contains data lines for m6A and m5C in human mRNA, using GRCh38 and Ensembl 110, then all sites must be inferred using the same technology.

  The best way to handle different detection technologies, treatment and/or conditions is to have as many dataset or bedRMod
  files as required to explicitly and unambiguously describe the metadata, in particular the experimental protocol, the bioinformatics
  workflow, and external sources.

The header section
^^^^^^^^^^^^^^^^^^

The header contains metainformation about the source of the data. All header fields are mandatory.

.. list-table:: bedRMod header
   :widths: 25 75
   :header-rows: 1

   * - Header field key
     - Prerequisite
   * - fileformat
     -
   * - organism
     -
   * - modification_type
     - Only RNA, refers to WTS or *whole transcriptome sequencing*
   * - modification_names
     -
   * - assembly
     - Only Ensembl nomenclature *e.g.* GRCh38
   * - annotation_source
     -
   * - annotation_version
     -
   * - sequencing_platform
     -
   * - basecalling
     -
   * - bioinformatics_workflow
     -
   * - experiment
     -
   * - external_source
     -

.. hint::

  For data upload, ``fileformat``, ``organism``, and ``assembly`` are validated. Only the latest or compatible specifications are used, and
  only ``modification_type=RNA`` is currently allowed. The ``assembly`` value must match exactly the assembly chosen from the dropdown menu
  during upload, and **it must follow the Ensembl nomenclature (without patch number)**. Data does not have to be for a specific genome assembly,
  Sci-ModoM will take care of lifting over all records to the most recent assembly for each organism.

  The values of ``short_name`` and ``primary_base`` given in ``modification_names`` are also validated and must match the standard
  `MODOMICS nomenclature <https://www.genesilico.pl/modomics/modifications>`_. If ``short_name`` contains a comma, entries must be
  double quoted, *e.g.* ``"28284:m6,6A:A","a:m6A:A"``. Sci-ModoM allows T for U and lowercase values, in addition
  to the existing nomenclature. Note that N is not a valid base.

  Additional user-defined key,value pairs or extra header lines starting with ``#`` are ignored during upload.

.. note::

   Sci-ModoM exports its data in compliance with the `MODOMICS nomenclature <https://www.genesilico.pl/modomics/modifications>`_. This
   means that values for ``name`` and ``primary_base`` of ``modification_names`` may differ from those originally uploaded. In practice,
   its always possible to *map* these using the original ``modification_names``, *i.e.* ``name`` to ``short_name``, and eventually T to U,
   or lowercase to uppercase variants.

   If there are additional entries in ``modification_names`` that do no match data lines, these are not written on export.
   If the file was created with `modkit <https://nanoporetech.github.io/modkit>`_, the content of ``bioinformatics_workflow`` remain however unchanged.

The data section
^^^^^^^^^^^^^^^^

The columns must be separated by tabs and each row must have the same number of columns.

.. list-table:: bedRMod data
   :widths: 25 175
   :header-rows: 1

   * - Data field
     - Prerequisite
   * - chrom
     - Only Ensembl short format
   * - chromStart
     -
   * - chromEnd
     -
   * - name
     - No name attributes are allowed
   * - score
     - Valid coverage (see below for details)
   * - strand
     -
   * - thickStart
     - Must be identical to chromStart
   * - thickEnd
     - Must be identical to chromEnd
   * - itemRgb
     -
   * - coverage
     -
   * - frequency
     -

.. hint::

  For data upload to Sci-ModoM, **chromosome names** (1st column) **must be written using the Ensembl short format** *e.g.* 1 and not chr1, or
  MT and not chrM. **Only chromosomes are considered, records from contigs or scaffolds are discarded**.

  The *valid coverage* should be used as a measure of confidence for score (5th column). This can be *e.g.* the number of calls passing filters
  (classified as modified and unmodified) at the reported modification position, as reported by `modkit <https://nanoporetech.github.io/modkit>`_ ,
  or the number or reads remaining after filtering and used to infer the modification status. In Sci-ModoM, **score is of type integer and must be greater than zero**.

  Coordinates for thickStart (7th column) and thickEnd (8th column) must be identical to chromStart and chromEnd, respectively.

.. caution::

  bedRMod is essentially a BED-formatted file, it uses a 0-based, half-open coordinate system. If you use a 1-based index, all your modification sites will be *off-by-one*!

.. warning::

  During upload, rows with invalid chromosomes are discarded. All names in the 4th column (or their corresponding short names) must be
  consistent with those chosen from the dropdown menu during upload. Rows with out-of-range values *e.g.* for score, coverage or frequency
  are discarded. Rows with inconsistent values for coordinates (chromStart/thickStart, chromEnd/thickEnd) are discarded.
  Dataset upload will fail if there are too many skipped records.

  A given detection technology is not supposed to yield different score, coverage, and frequency values for any given modification in any
  given organism, cell type, condition, *etc.* Consequently, duplicate records on chrom, chromStart, chromEnd, and strand for a given modification
  will cause a failure during upload. If the file was created with `modkit <https://nanoporetech.github.io/modkit>`_, users must be careful with the ``--motif`` option; if used only once, this should not duplicate records, and usage is documented in the header via ``bioinformatics_workflow``,
  but it is good practice to also mention it in the dataset description.

  Additional columns are ignored.


Notes
-----

Download
^^^^^^^^

A PDF version of the latest specification can be downloaded `here <https://dieterich-lab.github.io/euf-specs/>`_.
