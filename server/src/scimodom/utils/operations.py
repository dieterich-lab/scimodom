"""pybedtools
"""

from collections.abc import Sequence, Iterable
from typing import Any

import pybedtools  # type: ignore


def _to_bedtool(
    a_records: Iterable[Any], b_records: Iterable[Any], append: bool = True
):
    """Convert records to BedTool and sort

    :param a_records: DB records (A features)
    :type a_records: Iterable (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Iterable (list of tuples)
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


def get_intersection(
    a_records: Iterable[Any],
    b_records: Iterable[Any],
    s: bool = True,
    sorted: bool = True,
    n_fields: int = 3,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.intersect

    Relies on the behaviour of bedtools -wa -wb option: the first
    column after the complete -a record lists the file number
    from which the overlap came.

    :param a_records: DB records (A features)
    :type a_records: Iterable (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Iterable (list of tuples)
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
                    i.fields[(offset + 1) :],
                ),
                [],
            )
        )
        for i in c_bedtool
    ]
    return c_records


def get_closest(
    a_records: Iterable[Any],
    b_records: Iterable[Any],
    s: bool = True,
    sorted: bool = True,
    n_fields: int = 3,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.closest

    Relies on the behaviour of bedtools -io -t -mdb -D options: the first
    column after the complete -a record lists the file number
    from which the closest interval came.

    :param a_records: DB records (A features)
    :type a_records: Iterable (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Iterable (list of tuples)
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

    a_bedtool, b_bedtool = _to_bedtool(a_records, b_records)
    c_bedtool = a_bedtool.closest(
        b=[b.fn for b in b_bedtool], io=io, t=t, mdb=mdb, D=D, s=s, sorted=sorted
    )
    c_records = [
        tuple(
            sum(
                (
                    [i.chrom, i.start, i.end, i.name, i.score, i.strand],
                    i.fields[6:offset],
                    i.fields[(offset + 1) :],
                ),
                [],
            )
        )
        for i in c_bedtool
    ]
    return c_records


def get_subtract(
    a_records: Iterable[Any],
    b_records: Iterable[Any],
    s: bool = True,
    sorted: bool = True,
) -> list[Any]:
    """Wrapper for pybedtools.bedtool.BedTool.subtract

    :param a_records: DB records (A features)
    :type a_records: Iterable (list of tuples)
    :param b_records: DB records (B features)
    :type b_records: Iterable (list of tuples)
    :param s: Force strandedness
    :type s: bool
    :param sorted: Invoked sweeping algorithm
    :type sorted: bool
    :returns: c_records
    :rtype: list of tuples
    """

    a_bedtool, b_bedtool = _to_bedtool(a_records, b_records)
    c_bedtool = a_bedtool.subtract(b_bedtool, s=s, sorted=sorted)
    c_records = [
        (i.chrom, i.start, i.end, i.name, i.score, i.strand) for i in c_bedtool
    ]
    return c_records
