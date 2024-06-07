.. _euf:

bedRMod format
==============

The bedRMod format specification working group.

Version v1.7. June 2024


The bedRMod format specification
--------------------------------

The bedRMod, previously known as the EU (epitranscriptome unified data exchange) format is similar to the `ENCODE bedMethyl <https://www.encodeproject.org/data-standards/wgbs/>`_ format (BED9+2), but includes a header. The name (4th column) must conform to the `MODOMICS <https://www.genesilico.pl/modomics/modifications>`_ nomenclature for the modification short name, and the score (5th column) is a site-specific measure of confidence.

The bedRMod file is a tabulated count of base modifications from every sequencing read over each reference genomic position or modification site. It is a convenient representation of the information stored in the MM/ML tags in BAM alignment files.

.. note::

  Sci-ModoM requirements

  A given dataset or bedRMod file can contain more than one modification, as reported in column 4 (MODOMICS short name), but this should
  be for the same RNA type. Supported RNA types are *WTS* or *whole transcriptome sequencing* and *tRNA* or *transfer RNA*. A dataset or bedRMod
  file can only contain ONE RNA type, ONE technology, ONE organism (incl. cell type, tissue, or organ), and records from the same assembly.
  The best way to handle treatment and/or conditions is to have as many bedRMod files as required to describe the experimental protocol, and
  provide a meaningful title and metadata for each file.


.. attention::

  Format specification for tRNA

  Sci-ModoM currently does not handle tRNA annotation. We are actively working on this, and more information will be soon available...



The header section
^^^^^^^^^^^^^^^^^^

Each line starts with a ``#`` and contains the header tag and its value, separated by a ``=``, *e.g.* ``#fileformat=bedRModv1.7``.
As bedRMod contains data for only one organism, only one reference to organism, assembly, annotation source, and annotation version is possible.

.. list-table:: bedRMod header
   :widths: 50 75
   :header-rows: 1

   * - Tag
     - Description
   * - fileformat
     - Fileformat and version *e.g.* bedRModv1.7
   * - organism
     - NCBI taxid
   * - modification_type
     - RNA (or DNA)
   * - assembly
     - Assembly name using Ensembl nomenclature *e.g.* GRCh38 for human
   * - annotation_source
     - Annotation source *e.g.* Ensembl
   * - annotation_version
     - Annotation version *e.g.* 110
   * - sequencing_platform
     - Sequencing platform *e.g.* Illumina, ONT, *etc.*
   * - basecalling
     - Basecalling model information where relevant
   * - bioinformatics_workflow
     - Reference to bioinformatics workflow *e.g.* GitHub
   * - experiment
     - Information about experimental protocol, design, *etc.* or link to *e.g.* openBIS
   * - external_source
     - Databank;ID of data *e.g.* GEO;GSEXXXXXX


While all tags are required, ``sequencing_platform``, ``basecalling``, ``bioinformatics_workflow``, ``experiment`` or ``external_source`` can be left
empty *e.g.*

::

    #fileformat=bedRModv1.7
    #organism=9606
    #modification_type=RNA
    #assembly=GRCh38
    #annotation_source=Ensembl
    #annotation_version=110
    #sequencing_platform=Illumina NovaSeq 6000
    #basecalling=
    #bioinformatics_workflow=https://github.com/...
    #experiment=https://doi.org/...
    #external_source=GEO;GSEXXXXXX,PMID;XXXXXXXX

.. attention::

    For data upload to Sci-ModoM, ``fileformat``, ``organism``, and ``assembly`` are validated. Only the latest specifications are used, and only ``modification_type=RNA`` is allowed. The ``assembly`` tag entry must match exactly the chosen assembly and must follow the Ensembl nomenclature.
    Additional user-defined tags or extra header lines starting with ``#`` are ignored during upload.


The data section
^^^^^^^^^^^^^^^^

The first nine columns generally follow the standard `BED specification <https://samtools.github.io/hts-specs/BEDv1.pdf>`_, but the name (4th column) must conform to the `MODOMICS <https://www.genesilico.pl/modomics/modifications>`_ nomenclature for the modification short name, and the score (5th column) is a site-specific measure of confidence. The last two columns contain the coverage (10th column), or number of reads at this position, and the frequency (11th column), or the integer value capped at 100 representing the precentage of reads that are modified at this position. These columns must be separated by tabs and each row must have the same number of columns.

.. attention::

    For data upload to Sci-ModoM, chromosomes (1st column) must be formatted following the Ensembl short format *e.g.* 1 and not chr1, or MT and not chrM.
    Only chromosomes are considered, records from contigs/scaffolds are discarded. The modification name (4th column) must match exactly the chosen
    modifications, according to the `MODOMICS <https://www.genesilico.pl/modomics/modifications>`_ nomenclature for the modification short name. Rows with
    undefined strand (6th column) are discarded. Rows with out-of-range values for score (5th column) or frequency (11th column) are discarded.

.. warning::

    File upload will fail if there are too many skipped records.


Additional columns
""""""""""""""""""

Users can add any number of additional columns to suit their needs (same as for BED), but these are ignored in Sci-ModoM. Note however that a bedRMod
file with exactly 12 columns may be implicitely assumed to be a BED12 file by some software (bedtools, genome browsers, ...), which can result in
unexpected behaviour.


Notes
-----

Unmodified bases
^^^^^^^^^^^^^^^^^

bedRMod is a format to store modification data (site-specific or not), hence unmodified bases should not be recorded.
Context can be recorded using chromStart/End + thickStart/End, additional columns, *etc*.

Download
^^^^^^^^

A PDF version of the latest specification can be downloaded `here <https://github.com/anmabu/bedRMod/blob/587107220516b1f7f5dc645dafd771e9e1a2b289/bedRModv1.7.pdf>`_.
