
Data Specification​
==================

Current version v1.7, consult `bedRMod <https://github.com/anmabu/bedRMod/tree/main>`_. The file extension is ".bed" or ".bedrmod".

Notes
-----

Additional columns
^^^^^^^^^^^^^^^^^^

Users can add any number of additional columns to suit their needs (same as for BED), but these are ignored in Sci-ModoM. Note however that a bedRMod file with exactly 12 columns may be implicitely assumed to be a BED12 file by some software (bedtools, genome browsers, ...).

Unmodified bases
^^^^^^^^^^^^^^^^

bedRMod is a format to store modification data (site-specific or not), hence unmodified bases should not be recorded.
Context can be recorded using chromStart/End + thickStart/End, additional columns, *etc*.

General remarks
^^^^^^^^^^^^^^^

In Sci-ModoM, uploading data in bedRMod format requires each bedRMod to contain a single organism (species and cell, tissue, or organ) and a single technology. One bedRMod file can however contain more than one modification, as recorded by column 4.

If you file bedRmod file contains different data and/or additional columns to store information such as RNA type, experimental condition, *etc.*, you need to split your data such that individual bedRMod files can be uploaded with as much specific information as possible, *e.g. m6A in human cell type X using technology Y under treatment condition Z, etc.*
