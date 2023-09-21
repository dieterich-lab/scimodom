
Data Specification​
==================

Current version v1.6. Does not match `bedRMod <https://github.com/anmabu/bedRMod/tree/main>`_...
The file extension is ".bed" or ".bedrmod".

Notes
-----

Additional columns
^^^^^^^^^^^^^^^^^^

Additional columns are not mentioned in the specs. Users can add any number of additional columns, but they are not part of the specs. This is implicit (stems from BED: The BED format consists of one line per feature, each containing 3-12 columns of data, plus optional track definition lines).

Consensus definition for column 5 (score)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The definition of column 5 must remain general (e.g. modification confidence).

Remarks: *c.f.* SAM specs for base modification "the optional ML tag lists the probability of each modification listed in the MM tag being correct".

Unmodified bases
^^^^^^^^^^^^^^^^

bedRMod is a format to store modification data (site-specific or not), hence there should not be any unmodified bases.
Context can be recorded using chromStart/End + thickStart/End, additional columns, etc.


Missing Data
^^^^^^^^^^^^

No missing data for coverage.
Score: Use 0.
refBase: Use "." (leave N for unidentified nucleotide)


Optional header tags
^^^^^^^^^^^^^^^^^^^^

No optional tags, i.e. "#external_source" should be added in the specs as a mandatory field (with possibly empty value if not applicable), c.f. Table 3 Required Header Fields, or left out.


What is a valid header (for parsing)?​
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It was suggested that "#fileformat", "#organism", "#modification_type", "#assembly", "#annotation_source", "#annotation_version" should always be defined, the rest can have an empty value, e.g. "#basecalling=".
This should be explicit in the specs.


General remarks
^^^^^^^^^^^^^^^

One bedRMod = one organism ("#organism", "#assembly", "#annotation_source", "#annotation_version").
This should be explicit in the specs.

There is no other limitations, *.e.g.* for RNA type, organism, *etc.* it's up to the user to split into multiple bedRmod, or
record the information in additional columns, which can be used to eventually split the data. All these cases can be dealt with in Sci-ModoM,
leaving the actual specs more flexible.
