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


def to_bedtool(records, as_list: bool = False):
    """Convert records to BedTool and sort

    TODO: records can be str | Path | Sequence[Any], see below get_genomic_annotation!
    check https://daler.github.io/pybedtools/autodocs/pybedtools.bedtool.BedTool.html
    For testing, should we allow passing from_string?

    :param records: Database records (or list of records)
    :type records: Sequence
    :param as_list: Return results as a list of BedTool
    :type as_list: bool
    :return: bedtool
    :rtype: BedTool or list of BedTool
    """
    if as_list:
        bedtool = [pybedtools.BedTool(record).sort() for record in records]
    else:
        bedtool = pybedtools.BedTool(records).sort()
    return bedtool


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

    data_bedtool = to_bedtool(records)
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
    records: list[tuple[Any, ...]],
    chain_file: str,
    unmapped: str | None = None,
    chrom_id: str = "s",
) -> tuple[str, str]:
    """Liftover records. Handles conversion to BedTool, but not from,
    of the liftedOver features. A file is returned pointing
    to the liftedOver features. The unmapped ones are saved as
    "unmapped", or discarded.

    :param records: Data records to liftover
    :type records: List of tuple of (str, ...) - Data records
    :param chain_file: Chain file
    :type chain_file: str
    :param unmapped: File to write unmapped features
    :type unmapped: str or None
    :param chrom_id: The style of chromosome IDs (default s).
    :type chrom_id: str
    :returns: Files with liftedOver and unmapped features
    :rtype: tuple of (str, str)
    """
    bedtool = to_bedtool(records)
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
    return result, unmapped


def remove_filno(feature, n_fields: int = 9, is_closest: bool = False):
    """This function is to be passed
    as argument to BedTool.each(), to
    generate a BED-like Interval. This is used
    to "strip" the returned interval from the
    "additional column describing the file number"
    when calling intersect or closest (with -wa and
    -wb). The default format is BED6+3, where
    3 additional fields are "dataset_id", "coverage",
    and "frequency". For closest, distance is appended
    at the end.

    :param feature: A feature from a BED file.
    :type feature: pybedtools.Interval
    :param n_fields: BED format
    :type n_fields: int
    :param is_closest: Add distance field
    :type is_closest: bool
    :return: New interval
    :rtype: pybedtools interval
    """
    target = 2 * n_fields + int(is_closest)
    line = [f for f in feature.fields]
    if len(feature.fields) != target:
        line.pop(n_fields)
    return pybedtools.cbedtools.create_interval_from_list(line)


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
