"""Data classes mostly for type casting and "serialization"
of records returned from operations (pybedtools).
NOTE: Order of definition is important (should be guaranteed)!
"""

import scimodom.utils.utils as utils

from collections.abc import Sequence
from typing import NamedTuple, Any


def get_types(model: str) -> dict[str, Any]:
    """utils wrapper to get column types from ORM
    model definition

    :param model: Model (name)
    :type model: str
    :returns: dictionary column: type
    :rtype: dict
    """
    mapped_types = utils.get_table_column_python_types(model)
    mapped_columns = utils.get_table_columns(model)
    return dict(zip(mapped_columns, mapped_types))


class Subtract(NamedTuple):
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

    _dtypes = get_types("Data")

    chrom: _dtypes["chrom"]
    start: _dtypes["start"]
    end: _dtypes["end"]
    name: _dtypes["name"]
    score: _dtypes["score"]
    strand: _dtypes["strand"]
    dataset_id: _dtypes["dataset_id"]
    coverage: _dtypes["coverage"]
    frequency: _dtypes["frequency"]


class Intersect(NamedTuple):
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

    _dtypes = get_types("Data")

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


class Closest(NamedTuple):
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

    _dtypes = get_types("Data")

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
    distance: int


class GenomicAnnotation(NamedTuple):
    """Named tuple for GenomicAnnotation records.

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

    _dtypes = get_types("GenomicAnnotation")

    chrom: _dtypes["chrom"]
    start: _dtypes["start"]
    end: _dtypes["end"]
    gene_name: _dtypes["gene_name"]
    annotation_id: _dtypes["annotation_id"]
    strand: _dtypes["strand"]
    gene_id: _dtypes["gene_id"]
    gene_biotype: _dtypes["gene_biotype"]


def records_factory(instance_str: str, vals: Sequence[Any]):
    """Factory to conditionally instantiate records class

    :param op: instance_str (Subtract, Intersect, Closest, etc.)
    :type op: str
    :param vals: records
    :type vals: Sequence[Any]
    :returns: TypedRecords instance
    :rtype: TypedRecords
    """
    instance = eval(instance_str)

    class TypedRecords(instance):
        """Inherit from instance with forced type conversion."""

        def __new__(cls, *vals):
            super_obj = super(instance, cls)
            superclass = super_obj.__thisclass__
            typed_vals = [
                _dtype.__call__(val)
                for val, _dtype in zip(vals, superclass.__annotations__.values())
            ]
            return super_obj.__new__(cls, typed_vals)

    return TypedRecords(*vals)
