"""pybedtools
"""

from collections.abc import Sequence
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Any

import pybedtools  # type: ignore

import scimodom.utils.utils as utils

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

    a_bedtool, b_bedtool = _to_bedtool(a_records), _to_bedtool(
        utils.flatten_list(b_records)
    )
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
    pass
    # features = {
    #     "exon": "Exon",
    #     "five_prime_utr": "5'UTR",
    #     "three_prime_utr": "3'UTR",
    #     "CDS": "CDS",
    # }

    # def _gtf_to_records(bedtool):
    #     return [
    #         tuple(
    #             sum(
    #                 (
    #                     [i.chrom, i.start, i.end, i.name, annotation_id, i.strand],
    #                     [
    #                         parse_gtf_attributes(i.fields[8]).get(k)
    #                         for k in ["gene_id", "gene_biotype"]
    #                     ],
    #                 ),
    #                 [],
    #             )
    #         )
    #         for i in bedtool
    #     ]

    # def _clean_fields(field, delim=","):
    #     for f in field:
    #         if delim not in f:
    #             yield f
    #             continue
    #         yield None

    # def _to_records(bedtool, feature):
    #     return [
    #         tuple(
    #             sum(
    #                 (
    #                     [i.fields[4], i.fields[10], feature],
    #                     [
    #                         k
    #                         for k in _clean_fields(
    #                             [i.fields[9], i.fields[12], i.fields[13]]
    #                         )
    #                     ],
    #                 ),
    #                 [],
    #             )
    #         )
    #         for i in bedtool
    #     ]

    # def _intersect(data, stream, feature):
    #     bedtool = _to_bedtool(_gtf_to_records(stream))
    #     merged = bedtool.merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
    #     itrx = data.intersect(b=merged, wa=True, wb=True, s=True, sorted=True)
    #     return _to_records(itrx, feature)

    # all_records = []
    # tmpdir = pybedtools.helpers.get_tempdir()
    # with tempfile.TemporaryDirectory(dir=tmpdir) as tempdir:
    #     pybedtools.helpers.set_tempdir(tempdir)
    #     annotation = _to_bedtool(annotation_file)  # as gtf
    #     data_bedtool = _to_bedtool(records)
    #     for key, val in features.items():
    #         stream = annotation.filter(lambda a: a.fields[2] == key)
    #         all_records.append(_intersect(data_bedtool, stream, val))
    #     genes = annotation.filter(
    #         lambda a: a.fields[2] == "gene"
    #     ).saveas()  # "complement" see issue #49 for more
    #     exons = annotation.filter(lambda a: a.fields[2] == "exon")
    #     introns = genes.subtract(exons, s=True, sorted=True)
    #     all_records.append(_intersect(data_bedtool, introns, "Intron"))
    #     inter = genes.complement(g=chrom_file)
    #     itrx = data_bedtool.intersect(b=inter, wa=True, wb=True, s=False, sorted=True)
    #     itrx_records = [
    #         (i.fields[4], annotation_id, "Intergenic", None, None, None) for i in itrx
    #     ]
    #     all_records.append(itrx_records)
    # pybedtools.helpers.set_tempdir(tmpdir)
    # return utils.flatten_list(all_records)


def _get_annotation_from_file(
    annotation_file: Path, annotation_id: int, fmt: str, error
) -> list[tuple[str, int, str, str]]:
    """Create records for GenomicAnnotation from annotation file.
    Adds a "dummy" record for intergenic annotation.

    :param annotation_file: Annotation file
    :type annotation_file: Path
    :param annotation_id: Annotation ID
    :type annotation_id: int
    :param fmt: Annotation format
    :type fmt: str
    :param error: Format error to raise
    :type error: AnnotationFormatError
    :returns: Annotation as tuple of columns
    :rtype: list of tuples of (str,int,str,str)
    """
    suffixes = [s.replace(".", "") for s in annotation_file.suffixes]
    if fmt not in suffixes:
        msg = (
            f"Annotation file {annotation_file} does not appear to be in "
            f"the {fmt} format. Aborting transaction!"
        )
        raise error(msg)

    def _get_attrs(feature):
        # requires at least BED4 to avoid MalformedBedLineError...
        # return feature.attrs["gene_id"], annotation_id, feature.name, feature.attrs["gene_biotype"]
        return (
            feature.chrom,
            feature.start,
            feature.end,
            feature.name,
            feature.attrs["gene_id"],
            feature.attrs["gene_biotype"],
        )

    annotation = _to_bedtool(annotation_file)
    stream = annotation.filter(lambda f: f.fields[2] == "gene")
    stream = stream.each(_get_attrs)
    records = [(s[4], annotation_id, s[3], s[5]) for s in stream]
    prefix = utils.get_ensembl_prefix(records[0][0])
    records.append((f"{prefix}INTER", annotation_id, None, None))
    return records


def _liftover(
    records: list[dict[str, Any]],
    chain_file: str,
    unmapped: str | None = None,
    chrom_id: str = "s",
) -> str:
    """Liftover records. Handles conversion to BedTool, but not from,
    of the liftedOver features. Instead, a file is returned pointing
    to the liftedOver features. The unmapped ones are saved as
    "unmapped", or discarded.

    :param records: Data records to liftover
    :type records: dict of {str: Any}
    :param chain_file: Chain file
    :type chain_file: str
    :param unmapped: File to write unmapped features
    :type unmapped: str or None
    :param chrom_id: The style of chromosome IDs (default s).
    :typoe chrom_id: str
    """
    tmp = [tuple(r.values()) for r in records]
    bedtool = _to_bedtool(tmp)
    result = pybedtools.BedTool._tmp()
    if unmapped is None:
        unmapped = pybedtools.BedTool._tmp()
    cmd = f"CrossMap bed --chromid {chrom_id} --unmap-file {unmapped} {chain_file} {bedtool.fn} {result}"
    # set a timeout?
    try:
        subprocess.run(shlex.split(cmd), check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        msg = "Process failed: CrossMap executable could not be found!"
        raise Exception(msg) from exc
    except subprocess.CalledProcessError as exc:
        msg = f"Process failed with {exc.stderr}"
        raise Exception(msg) from exc
    # except subprocess.TimeoutExpired as exc:
    return result
