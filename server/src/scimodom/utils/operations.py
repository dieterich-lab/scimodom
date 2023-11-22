"""pybedtools
"""

from collections.abc import Sequence, Iterable
from typing import Any

import pybedtools  # type: ignore


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

    a_bedtool = pybedtools.BedTool(a_records).sort()
    b_bedtool = []
    for records in b_records:
        b_bedtool.append(pybedtools.BedTool(records).sort())
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
