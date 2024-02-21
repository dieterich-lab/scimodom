"""pybedtools
"""

from collections.abc import Sequence
import os
import logging
from pathlib import Path
import shlex
import subprocess
import tempfile
from typing import Any

import pybedtools  # type: ignore

import scimodom.utils.utils as utils

logger = logging.getLogger(__name__)


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
    annotation_path: Path, features: dict[str, str], records: Sequence[Any], error
) -> Sequence[Any]:
    """Annotate data records, i.e. create
    records for DataAnnotation. Columns
    order is (gene_id, data_id, feature).
    There is no type coercion.

    :param annotation_path: Path to annotation
    :type annotation_path: Path
    :param records: Data records as BED6+1-like,
    where the additional field is the "data_id".
    :type records: Sequence (list of tuples)
    :param features: Genomic features for which
    annotation must be created.
    :type features: dict of {str: str}
    :param error: Format error to raise
    :type error: AnnotationFormatError
    :returns: Records for DataAnnotation
    :rtype: Sequence (list of tuples)
    """

    def _intersect(annotation, feature):
        # delim (collapse) Default: ","
        stream = data_bedtool.intersect(
            b=annotation, wa=True, wb=True, s=True, sorted=True
        )
        return [
            (gene_id, s[6], feature)
            for s in stream
            for gene_id in s[13].split(",")
            if gene_id is not None
        ]

    data_bedtool = _to_bedtool(records)
    try:
        intergenic_feature = features.pop("intergenic")
    except KeyError as exc:
        msg = (
            "Missing feature intergenic from specs. This is due to a change "
            "in definition. Aborting transaction!"
        )
        raise error(msg) from exc
    all_records = []
    for feature, pretty_feature in features.items():
        filen = Path(annotation_path, f"{feature}.bed").as_posix()
        feature_bedtool = pybedtools.BedTool(filen)
        all_records.extend(_intersect(feature_bedtool, pretty_feature))

    # any feature_bedtool, exc. intergenic has a gene_id at fields 6...
    prefix = utils.get_ensembl_prefix(feature_bedtool[0].fields[6].split(",")[0])
    gene_id = f"{prefix}{intergenic_feature}"
    filen = Path(annotation_path, "intergenic.bed").as_posix()
    feature_bedtool = pybedtools.BedTool(filen)
    stream = data_bedtool.intersect(
        b=feature_bedtool, wa=True, wb=True, s=False, sorted=True
    )
    all_records.extend([(gene_id, s[6], intergenic_feature) for s in stream])
    return all_records


def write_annotation_to_bed(
    annotation_file: Path, chrom_file: Path, features: dict[str, list[str]], error
) -> None:
    """Prepare annotation in BED format for genomic
    features given in "features". The files are
    written to the parent directory of "annotation_file"
    using "features" as stem, and bed as extension.

    :param annotation_file: Path to annotation file.
    The format is implicitely assumed to be GTF.
    :type annotation_file: Path
    :param chrom_file: Path to chrom file
    :type chrom_file: Path
    :param features: Genomic features for which
    annotation must be created.
    :type features: dict of {str: list of str}
    :param error: Format error to raise
    :type error: AnnotationFormatError
    """
    parent = annotation_file.parent
    annotation_bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()

    msg = (
        f"Preparing annotation and writing to {parent}. This can take a few minutes..."
    )
    logger.debug(msg)

    def _annotation_to_stream(feature):
        return annotation_bedtool.filter(lambda a: a.fields[2] == feature).each(
            _get_gtf_attrs
        )

    tempdir = pybedtools.helpers.get_tempdir()
    try:
        with tempfile.TemporaryDirectory(dir=tempdir) as workdir:
            pybedtools.helpers.set_tempdir(workdir)
            for feature in features["conventional"]:
                filen = Path(parent, f"{feature}.bed").as_posix()
                _ = (
                    _annotation_to_stream(feature)
                    .merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
                    .moveto(filen)
                )
            feature = "intron"
            if feature not in features["extended"]:
                msg = (
                    f"Missing feature {feature} from specs. This is due to a change "
                    "in definition. Aborting transaction!"
                )
                raise error(msg)
            filen = Path(parent, "exon.bed").as_posix()
            exons = pybedtools.BedTool(filen)
            filen = Path(parent, f"{feature}.bed").as_posix()
            # why is the sort order lost after subtract?
            _ = (
                _annotation_to_stream("gene")
                .subtract(exons, s=True, sorted=True)
                .sort()
                .merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
            ).moveto(filen)
            feature = "intergenic"
            if feature not in features["extended"]:
                msg = (
                    f"Missing feature {feature} from specs. This is due to a change "
                    "in definition. Aborting transaction!"
                )
                raise error(msg)
            filen = Path(parent, f"{feature}.bed").as_posix()
            _ = (
                _annotation_to_stream("gene")
                .complement(g=chrom_file.as_posix())
                .moveto(filen)
            )
    except:
        raise
    finally:
        pybedtools.helpers.set_tempdir(tempdir)


def get_annotation_records(
    annotation_file: Path, annotation_id: int, intergenic_feature: str
) -> list[tuple[str, int, str, str]]:
    """Create records for GenomicAnnotation from
    annotation file. Columns order is
    (gene_id, annotation_id, gene_name, gene_biotype).
    There is no type coercion.

    :param annotation_file: Path to annotation file.
    The format is implicitely assumed to be GTF.
    :type annotation_file: Path
    :param annotation_id: Annotation ID
    :type annotation_id: int
    :param intergenic_feature: Name for intergenic
    feature. This name must come from Annotation
    specifications, as it must match that used
    when creating annotation for data records.
    :type intergenic_feature: str
    :returns: Annotation records as tuple of columns
    :rtype: list of tuples of (str, int, str, str)
    """
    msg = f"Creating annotation for {annotation_file}..."
    logger.debug(msg)

    bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
    stream = bedtool.filter(lambda f: f.fields[2] == "gene").each(_get_gtf_attrs)
    records = [(s[6], annotation_id, s[3], s[7]) for s in stream]
    # add a "dummy" record for intergenic annotation
    prefix = utils.get_ensembl_prefix(records[0][0])
    records.append((f"{prefix}{intergenic_feature}", annotation_id, None, None))
    return records


def liftover_to_file(
    records: list[dict[str, Any]],
    chain_file: str,
    unmapped: str | None = None,
    chrom_id: str = "s",
) -> str:
    """Liftover records. Handles conversion to BedTool, but not from,
    of the liftedOver features. A file is returned pointing
    to the liftedOver features. The unmapped ones are saved as
    "unmapped", or discarded.

    :param records: Data records to liftover
    :type records: dict of {str: Any}
    :param chain_file: Chain file
    :type chain_file: str
    :param unmapped: File to write unmapped features
    :type unmapped: str or None
    :param chrom_id: The style of chromosome IDs (default s).
    :type chrom_id: str
    :returns: File with liftedOver features
    :rtype: str
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
