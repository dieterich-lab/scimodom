"""pybedtools
"""

import os

from collections.abc import Sequence
from typing import Any

from pathlib import Path
from scimodom.utils.utils import flatten_list

import pybedtools  # type: ignore


if os.getenv("APP_TEMPDIR"):
    tempdir = os.environ["APP_TEMPDIR"]
    pybedtools.helpers.set_tempdir(tempdir)


def _to_bedtool(records, asl: bool = False):
    """Convert records to BedTool and sort

    TODO: records can be str | Path | Sequence[Any], see below get_genomic_annotation!
    check https://daler.github.io/pybedtools/autodocs/pybedtools.bedtool.BedTool.html
    For testing, should we allow passing from_string?

    :param records: Database records (or list of records)
    :type records: Sequence
    :returns: bedtool
    :rtype: BedTool or list of BedTool
    """
    if asl:
        bedtool = [pybedtools.BedTool(record).sort() for record in records]
    else:
        bedtool = pybedtools.BedTool(records).sort()
    return bedtool


def get_op(op: str):
    """Function selection

    :param op: operation
    :type op: str
    :returns: selected function
    :rtype: function
    """
    return eval(f"get_{op}")


def get_intersect(
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

    a_bedtool, b_bedtool = _to_bedtool(a_records), _to_bedtool(b_records, asl=True)
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

    a_bedtool, b_bedtool = _to_bedtool(a_records), _to_bedtool(b_records, asl=True)
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

    a_bedtool, b_bedtool = _to_bedtool(a_records), _to_bedtool(flatten_list(b_records))
    c_bedtool = a_bedtool.subtract(b_bedtool, s=s, sorted=sorted)
    # c_records = [(i.fields[:offset]) for i in c_bedtool]
    c_records = [tuple(i.fields[:offset]) for i in c_bedtool]
    return c_records


def get_genomic_annotation(
    annotation_file: str | Path,
    chrom_file: str | Path,
    annotation_id: int,
    records: Sequence[Any],
) -> list[Any]:
    """Create records for genomic annotation

    NOTE: 06.12.2023 GTF only! fields indices hard coded!
          Requires > ~3GB /tmp disk space

    :param annotation_file: Path to annotation (gtf)
    :type annotation_file: str | Path
    :param chrom_file: Path to chrom sizes
    :type chrom_file: str | Path
    :param annotation_id: Current annotation id (taxa, release, version)
    :type annotation_id: int
    :param records: DB records
    :type records: Sequence (list of tuples)
    :returns: Records for GenomicAnnotation
    :rtype: list of tuples
    """
    import tempfile
    from scimodom.utils.utils import flatten_list
    from scimodom.utils.utils import parse_gtf_attributes

    features = {
        "exon": "Exon",
        "five_prime_utr": "5'UTR",
        "three_prime_utr": "3'UTR",
        "CDS": "CDS",
    }

    def _gtf_to_records(bedtool):
        return [
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
            for i in bedtool
        ]

    def _clean_fields(field, delim=","):
        for f in field:
            if delim not in f:
                yield f
                continue
            yield None

    def _to_records(bedtool, feature):
        return [
            tuple(
                sum(
                    (
                        [i.fields[4], i.fields[10], feature],
                        [
                            k
                            for k in _clean_fields(
                                [i.fields[9], i.fields[12], i.fields[13]]
                            )
                        ],
                    ),
                    [],
                )
            )
            for i in bedtool
        ]

    def _intersect(data, stream, feature):
        bedtool = _to_bedtool(_gtf_to_records(stream))
        merged = bedtool.merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
        itrx = data.intersect(b=merged, wa=True, wb=True, s=True, sorted=True)
        return _to_records(itrx, feature)

    all_records = []
    tmpdir = pybedtools.helpers.get_tempdir()
    with tempfile.TemporaryDirectory(dir=tmpdir) as tempdir:
        pybedtools.helpers.set_tempdir(tempdir)
        annotation = _to_bedtool(annotation_file)  # as gtf
        data_bedtool = _to_bedtool(records)
        for key, val in features.items():
            stream = annotation.filter(lambda a: a.fields[2] == key)
            all_records.append(_intersect(data_bedtool, stream, val))
        genes = annotation.filter(
            lambda a: a.fields[2] == "gene"
        ).saveas()  # "complement" see issue #49 for more
        exons = annotation.filter(lambda a: a.fields[2] == "exon")
        introns = genes.subtract(exons, s=True, sorted=True)
        all_records.append(_intersect(data_bedtool, introns, "Intron"))
        inter = genes.complement(g=chrom_file)
        itrx = data_bedtool.intersect(b=inter, wa=True, wb=True, s=False, sorted=True)
        itrx_records = [
            (i.fields[4], annotation_id, "Intergenic", None, None, None) for i in itrx
        ]
        all_records.append(itrx_records)
    pybedtools.helpers.set_tempdir(tmpdir)
    return flatten_list(all_records)
