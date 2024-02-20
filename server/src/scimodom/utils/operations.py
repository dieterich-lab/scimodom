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


def annotate_data_to_records(
    annotation_file: Path,
    chrom_file: Path,
    records: Sequence[Any],
) -> Sequence[Any]:
    """Annotate data records, i.e. create
    records for DataAnnotation. Since this
    function is only called after creating
    annotation (GenomicAnnotation), the
    annotation file is implicitely assumed
    to be GTF-formatted.

    :param annotation_file: Path to annotation (GTF)
    :type annotation_file: Path
    :param chrom_file: Path to chrom file
    :type chrom_file: Path
    :param records: Data records
    :type records: Sequence (list of tuples)
    :returns: Records for DataAnnotation
    :rtype: Sequence (list of tuples)
    """
    # GTF features
    features = {
        "exon": "Exon",
        "five_prime_utr": "5'UTR",
        "three_prime_utr": "3'UTR",
        "CDS": "CDS",
    }

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

    def _intersect(data, annotation, feature):
        # delim (collapse) Default: ","
        stream = data.intersect(b=annotation, wa=True, wb=True, s=True, sorted=True)
        return [
            (gene_id, s[6], feature)
            for s in stream
            for gene_id in s[13].split(",")
            if gene_id is not None
        ]

    def _annotation_to_stream(feature):
        # cannot stream merge...
        return annotation_bedtool.filter(lambda a: a.fields[2] == feature).each(
            _get_gtf_attrs
        )

    all_records = []
    tempdir = pybedtools.helpers.get_tempdir()
    try:
        with tempfile.TemporaryDirectory(dir=tempdir) as workdir:
            pybedtools.helpers.set_tempdir(workdir)
            annotation_bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
            data_bedtool = _to_bedtool(records)
            for k, v in features.items():
                merged = _annotation_to_stream(k).merge(
                    s=True, c=[4, 5, 6, 7, 8], o="distinct"
                )
                all_records.extend(_intersect(data_bedtool, merged, v))
                print(f"DONE WITH {v}")
            exons = _annotation_to_stream("exon")
            # why is the sort order lost after subtract?
            introns = (
                _annotation_to_stream("gene")
                .subtract(exons, s=True, sorted=True)
                .sort()
                .merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
            )
            all_records.extend(_intersect(data_bedtool, introns, "Intron"))
            print("DONE WITH Introns")
            prefix = utils.get_ensembl_prefix(annotation_bedtool[0].attrs["gene_id"])
            gene_id = f"{prefix}INTER"
            inter = _annotation_to_stream("gene").complement(g=chrom_file.as_posix())
            stream = data_bedtool.intersect(
                b=inter, wa=True, wb=True, s=False, sorted=True
            )
            all_records.extend([(gene_id, s[6], "Intergenic") for s in stream])
            print("DONE WITH Intergenic")
    except:
        raise
    finally:
        pybedtools.helpers.set_tempdir(tempdir)
    return all_records


def get_annotation_to_records(
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
    bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
    stream = bedtool.filter(lambda f: f.fields[2] == "gene").each(_get_gtf_attrs)
    records = [(s[6], annotation_id, s[3], s[7]) for s in stream]
    prefix = utils.get_ensembl_prefix(records[0][0])
    records.append((f"{prefix}INTER", annotation_id, None, None))
    return records


def liftover_to_file(
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


def _get_gtf_attrs(feature):
    """This function is to be passed
    as argument to BedTool.each(), to
    generate a BED-like Interval. The
    format is BED6+2, where 2 additional
    fields are "gene_id", "gene_biotype".

    Note: The value in Interval.start will
    always contain the 0-based start position,
    even if it came from a GFF or other 1-based
    feature. The contents of Interval.fields
    will always be strings, which in turn always
    represent the original line in the file.

    :param feature: A feature from a GTF file.
    :type feature: pybedtools.Interval
    """
    line = [
        feature.chrom,
        feature.start,
        feature.end,
        feature.name,
        feature.score,
        feature.strand,
        feature.attrs["gene_id"],
        feature.attrs["gene_biotype"],
    ]
    return pybedtools.cbedtools.create_interval_from_list(line)
