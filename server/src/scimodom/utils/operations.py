"""pybedtools
"""

import pybedtools


def get_intersection(a_records, b_records, wa=True, wb=True, s=True, sorted=True):
    """Wrapper for pybedtools.bedtool.BedTool.intersect"""

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
                ([i.chrom, i.start, i.end, i.name, i.score, i.strand], i.fields[6:]), []
            )
        )
        for i in c_bedtool
    ]
    return c_records
