"""pybedtools
"""

from collections.abc import Sequence
from typing import Any

from pathlib import Path
from scimodom.utils.utils import flatten_list

import pybedtools  # type: ignore


def _to_bedtool(
    a_records: Sequence[Any], b_records: Sequence[Any], append: bool = True
):
    """Convert records to BedTool and sort

    :param a_records: DB records (A features)
    :type a_records: Sequence (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Sequence (list of tuples)
    :returns: a_bedtool, b_bedtool
    :rtype: BedTool or list of BedTool
    """
    a_bedtool = pybedtools.BedTool(a_records).sort()
    if append:
        b_bedtool = []
        for records in b_records:
            b_bedtool.append(pybedtools.BedTool(records).sort())
    else:
        b_bedtool = pybedtools.BedTool(b_records).sort()
    return a_bedtool, b_bedtool


def get_op(op: str):
    """Function selection

    :param op: operation
    :type op: str
    :returns: selected function
    :rtype: function
    """
    if op == "intersect":
        return get_intersection
    elif op == "closest":
        return get_closest
    elif op == "subtract":
        return get_subtract


def get_intersection(
    a_records: Sequence[Any],
    b_records: Sequence[Any],
    s: bool = True,
    sorted: bool = True,
    n_fields: int = 3,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.intersect

    Relies on the behaviour of bedtools -wa -wb option: the first
    column after the complete -a record lists the file number
    from which the overlap came.

    :param a_records: DB records (A features)
    :type a_records: Sequence (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Sequence (list of tuples)
    :param s: Force strandedness
    :type s: bool
    :param sorted: Invoked sweeping algorithm
    :type sorted: bool
    :param n_fields: Number of other fields attribute in addition to BED6
    :type n_fields: int
    :returns: c_records
    :rtype: list of tuples
    """

    # required options
    # write the original entry in A for each overlap
    wa: bool = True
    # write the original entry in B for each overlap
    wb: bool = True

    # file number index
    offset = 6 + n_fields
    filnum_idx = 1
    if len(b_records) == 1:
        filnum_idx = 0

    a_bedtool, b_bedtool = _to_bedtool(a_records, b_records)
    c_bedtool = a_bedtool.intersect(
        b=[b.fn for b in b_bedtool], wa=wa, wb=wb, s=s, sorted=sorted
    )
    c_records = [
        tuple(
            sum(
                (
                    [i.chrom, i.start, i.end, i.name, i.score, i.strand],
                    i.fields[6:offset],
                    i.fields[(offset + filnum_idx) :],
                ),
                [],
            )
        )
        for i in c_bedtool
    ]
    return c_records


def get_closest(
    a_records: Sequence[Any],
    b_records: Sequence[Any],
    s: bool = True,
    sorted: bool = True,
    n_fields: int = 3,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.closest

    Relies on the behaviour of bedtools -io -t -mdb -D options: the first
    column after the complete -a record lists the file number
    from which the closest interval came.

    :param a_records: DB records (A features)
    :type a_records: Sequence (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Sequence (list of tuples)
    :param s: Force strandedness
    :type s: bool
    :param sorted: Invoked sweeping algorithm
    :type sorted: bool
    :param n_fields: Number of other fields attribute in addition to BED6
    :type n_fields: int
    :returns: c_records
    :rtype: list of tuples
    """

    # required options
    # Ignore features in B that overlap A
    io: bool = True
    # Report all ties
    t: str = "all"
    # Report closest records among all databases
    mdb: str = "all"
    # Report distance with respect to A
    D: str = "a"

    # file number index
    offset = 6 + n_fields
    filnum_idx = 1
    if len(b_records) == 1:
        filnum_idx = 0

    a_bedtool, b_bedtool = _to_bedtool(a_records, b_records)
    c_bedtool = a_bedtool.closest(
        b=[b.fn for b in b_bedtool], io=io, t=t, mdb=mdb, D=D, s=s, sorted=sorted
    )

    # Reports “none” for chrom (?) and “-1” for all other fields (?) when a feature
    # is not found in B on the same chromosome as the feature in A.
    # Note that "start" (fields) is a string!
    c_bedtool = c_bedtool.filter(lambda c: c.fields[(offset + filnum_idx + 1)] != "-1")
    c_records = [
        tuple(
            sum(
                (
                    [i.chrom, i.start, i.end, i.name, i.score, i.strand],
                    i.fields[6:offset],
                    i.fields[(offset + filnum_idx) :],
                ),
                [],
            )
        )
        for i in c_bedtool
    ]
    return c_records


def get_subtract(
    a_records: Sequence[Any],
    b_records: Sequence[Any],
    s: bool = True,
    sorted: bool = True,
    n_fields: int = 3,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.subtract

    :param a_records: DB records (A features)
    :type a_records: Sequence (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Sequence (list of tuples)
    :param s: Force strandedness
    :type s: bool
    :param sorted: Invoked sweeping algorithm
    :type sorted: bool
    :param n_fields: Number of other fields attribute in addition to BED6
    :type n_fields: int
    :returns: c_records
    :rtype: list of tuples
    """

    # file number index
    offset = 6 + n_fields

    a_bedtool, b_bedtool = _to_bedtool(a_records, flatten_list(b_records), append=False)
    c_bedtool = a_bedtool.subtract(b_bedtool, s=s, sorted=sorted)
    c_records = [(i.fields[:offset]) for i in c_bedtool]
    return c_records


def get_genomic_annotation(filen: str | Path, annotation_id: int) -> list[Any]:
    """Create records for genomic annotation

    NOTE: 06.12.2023 GTF only! fields indices hard coded!

    :param filen: Path to annotation (gtf)
    :type filen: str | Path
    :param annotation_id: Current annotation id (taxa, release, version)
    :type annotation_id: int
    :returns: GTF fields as BED+ records
    :rtype: list of tuples (records)
    """
    from scimodom.utils.utils import parse_gtf_attributes

    annotation = pybedtools.BedTool(filen).sort()
    genes = annotation.filter(lambda a: a.fields[2] == "gene")

    records = [
        tuple(
            sum(
                (
                    [i.chrom, i.start, i.end, i.name, annotation_id, i.strand],
                    [
                        parse_gtf_attributes(i.fields[8]).get(k)
                        for k in ["gene_id", "gene_biotype"]
                    ],
                ),
                [],
            )
        )
        for i in genes
    ]

    return records
