"""Data structures used in queries.
"""

import scimodom.utils.utils as utils

from typing import NamedTuple


class IntxRecords(NamedTuple):
    """Named tuple for twice BED6+3 records arrising
    from intersecting with -wa and -wb options.

    :param chrom: Chromosome
    :type chrom: Inferred from Data (str)
    :param start: start
    :type start: Inferred from Data (int)
    :param end: end
    :type end: Inferred from Data (int)
    :param score: score
    :type score: Inferred from Data (int)
    :param strand: strand
    :type strand: Inferred from Data (str)
    :param dataset_id: dataset_id
    :type dataset_id: Inferred from Data (str)
    :param coverage: coverage
    :type coverage: Inferred from Data (int)
    :param frequency: frequency
    :type frequency: Inferred from Data (int)
    """

    mapped_types = utils.get_table_column_python_types("Data")
    mapped_columns = utils.get_table_columns("Data")
    _dtypes = dict(zip(mapped_columns, mapped_types))

    chrom: _dtypes["chrom"]
    start: _dtypes["start"]
    end: _dtypes["end"]
    name: _dtypes["name"]
    score: _dtypes["score"]
    strand: _dtypes["strand"]
    dataset_id: _dtypes["dataset_id"]
    coverage: _dtypes["coverage"]
    frequency: _dtypes["frequency"]
    chrom_b: _dtypes["chrom"]
    start_b: _dtypes["start"]
    end_b: _dtypes["end"]
    name_b: _dtypes["name"]
    score_b: _dtypes["score"]
    strand_b: _dtypes["strand"]
    dataset_id_b: _dtypes["dataset_id"]
    coverage_b: _dtypes["coverage"]
    frequency_b: _dtypes["frequency"]


class TypedIntxRecords(IntxRecords):
    """Inherit from IntxRecords with forced type conversion."""

    def __new__(cls, *vals):
        super_obj = super(IntxRecords, cls)
        superclass = super_obj.__thisclass__
        typed_vals = [
            _dtype.__call__(val)
            for val, _dtype in zip(vals, superclass.__annotations__.values())
        ]
        return super_obj.__new__(cls, typed_vals)
