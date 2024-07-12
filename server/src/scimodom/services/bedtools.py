from functools import cache
import logging
from os import makedirs
from pathlib import Path
from typing import Iterable, Sequence, Any

import pybedtools  # type: ignore
from pybedtools import BedTool, create_interval_from_list

import scimodom.utils.utils as utils
from scimodom.config import get_config
from scimodom.database.models import Data
from scimodom.utils.bedtools_dto import (
    EufRecord,
    DataAnnotationRecord,
    GenomicAnnotationRecord,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
    ComparisonRecord,
)
from scimodom.utils.common_dto import Strand

logger = logging.getLogger(__name__)


class AnnotationFormatError(Exception):
    """Exception handling for change in specifications
    arising from Annotation when performing bedtools
    operations."""

    pass


def _get_gtf_attrs(feature):
    """This function is to be passed
    as argument to BedTool.each(), to
    generate a BED-like Interval. The
    format is BED6+2, where 2 additional
    fields are "gene_id", "gene_biotype".

    Note: The value in 'Interval.start' will
    always contain the 0-based start position,
    even if it came from a GFF or other 1-based
    feature. The contents of 'Interval.fields'
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


def _remove_filno(feature, n_fields: int = 9, is_closest: bool = False):
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


class BedToolsService:
    def __init__(self, tmp_path):
        makedirs(tmp_path, exist_ok=True)
        pybedtools.helpers.set_tempdir(tmp_path)

    @staticmethod
    def create_temp_file_from_records(
        records: Iterable[Sequence[Any]], sort: bool = True
    ) -> str:
        """Create a bedtool object from records.

        :param records: A iterable over records which can be processed by bedtools
        :type records: Iterable[Sequence[Any]]
        :param sort: sort the result
        :type sort: bool
        :returns: Path to temporary file
        :rtype: str
        """
        bedtool = BedTool(records)
        if sort:
            bedtool = bedtool.sort()
        return bedtool.fn

    @staticmethod
    def get_ensembl_annotation_records(
        annotation_file: Path, annotation_id: int, intergenic_feature: str
    ) -> Iterable[GenomicAnnotationRecord]:
        """Create records for GenomicAnnotation from
        annotation file. Columns order is
        (gene_id, annotation_id, gene_name, gene_biotype).

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
        :rtype: Iterable[GenomicAnnotationRecord]
        """
        logger.info(f"Creating annotation for {annotation_file}...")

        bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
        stream = bedtool.filter(lambda f: f.fields[2] == "gene").each(_get_gtf_attrs)
        prefix = None
        for s in stream:
            yield GenomicAnnotationRecord(
                id=s[6], annotation_id=annotation_id, name=s[3], biotype=s[7]
            )
            if prefix is None:
                # get a "dummy" record for intergenic annotation
                prefix = utils.get_ensembl_prefix(s[6])
        yield GenomicAnnotationRecord(
            id=f"{prefix}{intergenic_feature}", annotation_id=annotation_id
        )

    @staticmethod
    def get_gtrnadb_annotation_records(
        annotation_file: Path,
        annotation_id: int,
        organism: str,
    ) -> Iterable[GenomicAnnotationRecord]:
        """Create records for GenomicAnnotation from
        annotation file. Columns order is
        (gene_id, annotation_id, gene_name, gene_biotype).

        :param annotation_file: Path to annotation file.
        The format is implicitely assumed to be BED12.
        :type annotation_file: Path
        :param annotation_id: Annotation ID
        :type annotation_id: int
        :param organism: Organism name
        :type organism: str
        :returns: Annotation records as tuple of columns
        :rtype: Iterable[GenomicAnnotationRecord]
        """
        logger.info(f"Creating annotation for {annotation_file}...")

        bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
        for interval in bedtool:
            yield GenomicAnnotationRecord(
                id=f"{organism}_{interval.name}",
                annotation_id=annotation_id,
                name=interval.name,
                biotype="tRNA",
            )

    @staticmethod
    def gtrnadb_to_bed_features(annotation_file: Path, features: list[str]) -> None:
        """Wrangle GtRNAdb (BED12) annotation to BED format for
        each genomic features in "features". The files are
        written to the parent directory of "annotation_file"
        using "features" as stem, and bed as extension.

        NOTE: "features" are only used to validate consistency
        with the caller: only exon and intron are defined
        in this method.

        :param annotation_file: Path to annotation file.
        The format is implicitely assumed to be BED12.
        :type annotation_file: Path
        :param features: Genomic features for which
        annotation must be created.
        :type features: list of str
        """
        parent = annotation_file.parent
        annotation_bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()
        annotation_bed6 = annotation_bedtool.bed6()

        logger.info(f"Preparing annotation and writing to {parent}...")

        try:
            features.remove("exon")
            logger.debug("Writing exon...")
            file_name = Path(parent, "exon.bed").as_posix()
            _ = annotation_bed6.merge(s=True, c=[4, 5, 6], o="distinct").moveto(
                file_name
            )
        except ValueError:
            raise AnnotationFormatError(
                "Missing feature exon from specs. This is due to a change in definition."
            )

        try:
            features.remove("intron")
            logger.debug("Writing intron...")
            file_name = Path(parent, "intron.bed").as_posix()
            # assumes a simple file with non-overlapping exons which should be the case for tRNAs...
            _ = (
                annotation_bedtool.introns()
                .merge(s=True, c=[4, 5, 6], o="distinct")
                .moveto(file_name)
            )
        except ValueError:
            raise AnnotationFormatError(
                "Missing feature intron from specs. This is due to a change in definition."
            )

        try:
            features.pop()
            raise AnnotationFormatError(
                "Handling feature is not implemented. This is due to a change in definition."
            )
        except IndexError:
            pass

    def create_temp_euf_file(self, records: Iterable[EufRecord]) -> str:
        """Create a bedtool object from EUF records.

        :param records: A iterable over EUF records which can be processed by bedtools
        :type records: Iterable[EufRecord]
        :returns: Path to temporary file
        :rtype: str
        """

        def generator():
            for record in records:
                yield create_interval_from_list(
                    [
                        record.chrom,
                        record.start,
                        record.end,
                        record.name,
                        record.score,
                        record.strand.value,
                        record.thick_start,
                        record.thick_end,
                        record.item_rgb,
                        record.coverage,
                        record.frequency,
                    ]
                )

        return self.create_temp_file_from_records(generator())

    def annotate_data_using_ensembl(
        self,
        annotation_path: Path,
        features: dict[str, str],
        records: Iterable[Data],
    ) -> Iterable[DataAnnotationRecord]:
        """Annotate data records, i.e. create
        records for DataAnnotation. Columns
        order is (gene_id, data_id, feature).
        There is no type coercion.

        :param annotation_path: Path to annotation
        :type annotation_path: Path
        :param records: Data records as BED6+1-like,
        where the additional field is the "data_id".
        :type records: Iterable[Data]
        :param features: Genomic features for which
        annotation must be created.
        :type features: dict of {str: str}
        :returns: Records for DataAnnotation
        :rtype: Iterable[ModificationRecord]
        """

        bedtool_records = self._get_data_as_bedtool_for_annotation(records)
        if "intergenic" not in features:
            raise AnnotationFormatError(
                "Missing feature intergenic from specs. This is due to a change "
                "in definition. Aborting transaction!"
            )
        intergenic_feature = features.pop("intergenic")
        prefix = None
        for feature, pretty_feature in features.items():
            file_name = Path(annotation_path, f"{feature}.bed").as_posix()
            feature_bedtool = pybedtools.BedTool(file_name)
            if prefix is None:
                # any feature_bedtool, exc. intergenic has a gene_id at fields 6...
                prefix = utils.get_ensembl_prefix(
                    feature_bedtool[0].fields[6].split(",")[0]
                )
            for item in self._intersect_for_annotation(
                bedtool_records, feature_bedtool, pretty_feature
            ):
                yield item

        gene_id = f"{prefix}{intergenic_feature}"
        file_name = Path(annotation_path, "intergenic.bed").as_posix()
        feature_bedtool = pybedtools.BedTool(file_name)
        stream = bedtool_records.intersect(
            b=feature_bedtool, wa=True, wb=True, s=False, sorted=True
        )
        for s in stream:
            yield DataAnnotationRecord(
                gene_id=gene_id, data_id=s[6], feature=intergenic_feature
            )

    def ensembl_to_bed_features(
        self, annotation_file: Path, chrom_file: Path, features: dict[str, list[str]]
    ) -> None:
        """Wrangle Ensembl (GTF) annotation to BED format for
        each genomic features in "features". The files are
        written to the parent directory of "annotation_file"
        using "features" as stem, and bed as extension.

        NOTE: "extended features" are used to validate consistency
        with the caller: "conventional features" are extracted
        on the fly, but intron and intergenic require special treatment.

        :param annotation_file: Path to annotation file.
        The format is implicitely assumed to be GTF.
        :type annotation_file: Path
        :param chrom_file: Path to chrom file
        :type chrom_file: Path
        :param features: Genomic features for which
        annotation must be created.
        :type features: dict of {str: list of str}
        """
        parent = annotation_file.parent
        annotation_bedtool = pybedtools.BedTool(annotation_file.as_posix()).sort()

        logger.info(f"Preparing annotation and writing to {parent}...")

        for feature in features["conventional"]:
            logger.debug(f"Writing {feature}...")

            file_name = Path(parent, f"{feature}.bed").as_posix()
            _ = (
                self._annotation_to_stream(annotation_bedtool, feature)
                .merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
                .moveto(file_name)
            )

        file_name = Path(parent, "exon.bed").as_posix()
        exons = pybedtools.BedTool(file_name)
        file_name = self._check_feature("intron", features, parent)
        # why is the sort order lost after subtract?
        _ = (
            self._annotation_to_stream(annotation_bedtool, "gene")
            .subtract(exons, s=True, sorted=True)
            .sort()
            .merge(s=True, c=[4, 5, 6, 7, 8], o="distinct")
        ).moveto(file_name)

        file_name = self._check_feature("intergenic", features, parent)
        _ = (
            self._annotation_to_stream(annotation_bedtool, "gene")
            .complement(g=chrom_file.as_posix())
            .moveto(file_name)
        )

    def intersect(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
        is_sorted: bool = True,
    ) -> Iterable[IntersectRecord]:
        """Wrapper for pybedtools.bedtool.BedTool.intersect

        Relies on the behaviour of bedtools -wa -wb option: the first
        column after the complete -a record lists the file number
        from which the overlap came.

        :param a_records: Left operand of insect operation
        :type a_records: Iterable[ComparisonRecord]
        :param b_records_list: Right operand of insect operation
        :type b_records_list: list[Iterable[ModificationRecord]]
        :parm is_strand: Perform strand-aware query
        :type is_strand: bool
        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        a_bedtool = self._get_modifications_as_bedtool(a_records)
        b_bedtools = [self._get_modifications_as_bedtool(x) for x in b_records_list]
        bedtool = a_bedtool.intersect(
            b=[b.fn for b in b_bedtools],
            wa=True,  # write the original entry in A for each overlap
            wb=True,  # write the original entry in B for each overlap
            s=is_strand,
            sorted=is_sorted,
        )
        stream = bedtool.each(_remove_filno)
        for s in stream:
            a = self._get_modification_from_bedtools_data(s[:9])
            b = self._get_modification_from_bedtools_data(s[9:])
            r = IntersectRecord(a=a, b=b)
            yield r

    def closest(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
        is_sorted: bool = True,
    ) -> Iterable[ClosestRecord]:
        """Wrapper for pybedtools.bedtool.BedTool.closest

        Relies on the behaviour of bedtools -io -t -mdb -D options: the first
        column after the complete -a record lists the file number
        from which the closest interval came.

        :param a_records: Left operand of operation
        :type a_records: Iterable[ComparisonRecord]
        :param b_records_list: Right operand of operation
        :type b_records_list: list[Iterable[ModificationRecord]]
        :parm is_strand: Perform strand-aware query
        :type is_strand: bool
        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        # BED6+3
        n_fields = 9

        a_bedtool = self._get_modifications_as_bedtool(a_records)
        b_bedtools = [self._get_modifications_as_bedtool(x) for x in b_records_list]
        bedtool = a_bedtool.closest(
            b=[b.fn for b in b_bedtools],
            io=True,  # Ignore features in B that overlap A
            t="all",  # Report all ties
            mdb="all",  # Report closest records among all databases
            D="a",  # Report distance with respect to A
            s=is_strand,
            sorted=is_sorted,
        )
        # Reports “none” for chrom (.) and “-1” for all other fields (start/end) when a feature
        # is not found in B on the same chromosome as the feature in A.
        stream = bedtool.each(_remove_filno, is_closest=True).filter(
            lambda c: c.fields[n_fields + 1] != "-1"
        )
        for s in stream:
            yield ClosestRecord(
                a=self._get_modification_from_bedtools_data(s[:9]),
                b=self._get_modification_from_bedtools_data(s[9:18]),
                distance=s[18],
            )

    def subtract(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
        is_sorted: bool = True,
    ) -> Iterable[SubtractRecord]:
        """Wrapper for pybedtools.bedtool.BedTool.subtract

        :param a_records: Left operand of operation
        :type a_records: Iterable[ComparisonRecord]
        :param b_records_list: Right operand of operation
        :type b_records_list: Iterable[ModificationRecord]
        :parm is_strand: Perform strand-aware query
        :type is_strand: bool
        :param is_sorted: Invoked sweeping algorithm
        :type is_sorted: bool
        :returns: records
        :rtype: list of tuples
        """

        def b_generator():
            for records in b_records_list:
                for r in records:
                    yield r

        a_bedtool = self._get_modifications_as_bedtool(a_records)
        b_bedtool = self._get_modifications_as_bedtool(b_generator())
        bedtool = a_bedtool.subtract(b_bedtool, s=is_strand, sorted=is_sorted)
        for s in bedtool:
            yield SubtractRecord(**self._get_modification_from_bedtools_data(s).dict())

    @staticmethod
    def _annotation_to_stream(annotation_bedtool, feature):
        return annotation_bedtool.filter(lambda a: a.fields[2] == feature).each(
            _get_gtf_attrs
        )

    @staticmethod
    def _check_feature(feature, features, parent):
        if feature not in features["extended"]:
            raise AnnotationFormatError(
                f"Missing feature {feature} from specs. This is due to a change in definition."
            )
        logger.debug(f"Writing {feature}...")
        return Path(parent, f"{feature}.bed").as_posix()

    @staticmethod
    def _get_data_as_bedtool_for_annotation(
        records: Iterable[Data],
    ) -> BedTool:
        def generator():
            for record in records:
                yield create_interval_from_list(
                    [
                        record.chrom,
                        record.start,
                        record.end,
                        record.name,
                        record.score,
                        record.strand.value,
                        record.id,
                    ]
                )

        return BedTool(generator()).sort()

    @staticmethod
    def _intersect_for_annotation(bedtool_records, feature_bedtool, feature):
        # delim (collapse) Default: ","
        stream = bedtool_records.intersect(
            b=feature_bedtool, wa=True, wb=True, s=True, sorted=True
        )
        for s in stream:
            for gene_id in s[13].split(","):
                yield DataAnnotationRecord(
                    gene_id=gene_id, data_id=s[6], feature=feature
                )

    @staticmethod
    def _get_modifications_as_bedtool(
        records: Iterable[ComparisonRecord],
    ) -> BedTool:
        def generator():
            for record in records:
                yield create_interval_from_list(
                    [
                        record.chrom,
                        record.start,
                        record.end,
                        record.name,
                        record.score,
                        record.strand.value,
                        record.eufid,
                        record.coverage,
                        record.frequency,
                    ]
                )

        return BedTool(generator()).sort()

    @staticmethod
    def _get_modification_from_bedtools_data(s: Sequence[str]):
        return ComparisonRecord(
            chrom=s[0],
            start=s[1],
            end=s[2],
            name=s[3],
            score=s[4],
            strand=Strand(s[5]),
            eufid=s[6],
            coverage=s[7],
            frequency=s[8],
        )


@cache
def get_bedtools_service():
    return BedToolsService(tmp_path=get_config().BEDTOOLS_TMP_PATH)
