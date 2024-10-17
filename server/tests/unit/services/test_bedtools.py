import pytest

from pybedtools import BedTool

from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.bedtools import BedToolsService
from scimodom.utils.dtos.bedtools import (
    EufRecord,
    ComparisonRecord,
    Bed6Record,
)
from scimodom.utils.specs.enums import Strand

FEATURES = EnsemblAnnotationService.FEATURES


@pytest.fixture
def bedtools_service(tmp_path):
    yield BedToolsService(tmp_path=tmp_path)


def test_get_bed6_record_from_bedtool():
    record = BedToolsService._get_bed6_record_from_bedtool(
        [
            "1",
            "1043431",
            "1043432",
            "Y",
            "190",
            Strand.FORWARD,
        ]
    )
    assert isinstance(record, Bed6Record)
    assert record.chrom == "1"
    assert record.start == 1043431
    assert record.end == 1043432
    assert record.name == "Y"
    assert record.score == 190
    assert record.strand == Strand.FORWARD


def test_get_comparison_record_from_bedtool():
    record = BedToolsService._get_comparison_record_from_bedtool(
        [
            "1",
            "1043431",
            "1043432",
            "Y",
            "190",
            Strand.FORWARD,
            "iMuwPsi24Yka",
            "576",
            "19",
        ]
    )
    assert isinstance(record, ComparisonRecord)
    assert record.chrom == "1"
    assert record.start == 1043431
    assert record.end == 1043432
    assert record.name == "Y"
    assert record.score == 190
    assert record.strand == Strand.FORWARD
    assert record.eufid == "iMuwPsi24Yka"
    assert record.coverage == 576
    assert record.frequency == 19


def test_get_bed6_record_to_bedtool():
    bedtool = BedToolsService._get_bed6_record_to_bedtool(
        [
            Bed6Record(
                chrom="1",
                start=1043431,
                end=1043432,
                name="Y",
                score=190,
                strand=Strand.FORWARD,
            ),
            Bed6Record(
                chrom="1",
                start=1031,
                end=1032,
                name="Y",
                score=0,
                strand=Strand.REVERSE,
            ),
        ]
    )
    assert isinstance(bedtool, BedTool)
    # All features have chrom, start, stop, name, score, and strand attributes.
    # Note that start and stop are integers, while everything else (including score) is a string.
    # https://daler.github.io/pybedtools/intervals.html
    expected_records = [(1031, "0", "-"), (1043431, "190", "+")]
    for record, expected_record in zip(bedtool, expected_records):
        assert record.chrom == "1"
        assert record.start == expected_record[0]
        assert record.score == expected_record[1]
        assert record.strand == expected_record[2]


def test_get_comparison_record_to_bedtool():
    bedtool = BedToolsService._get_comparison_record_to_bedtool(
        [
            ComparisonRecord(
                chrom="1",
                start=1043431,
                end=1043432,
                name="Y",
                score=190,
                strand=Strand.FORWARD,
                eufid="iMuwPsi24Yka",
                coverage=576,
                frequency=19,
            ),
            ComparisonRecord(
                chrom="1",
                start=1031,
                end=1032,
                name="Y",
                score=0,
                strand=Strand.FORWARD,
                eufid="iMuwPsi24Yka",
                coverage=57,
                frequency=1,
            ),
        ]
    )
    assert isinstance(bedtool, BedTool)
    # All features have chrom, start, stop, name, score, and strand attributes.
    # Note that start and stop are integers, while everything else (including score) is a string.
    # https://daler.github.io/pybedtools/intervals.html
    expected_records = [(1031, "0", "1"), (1043431, "190", "19")]
    for record, expected_record in zip(bedtool, expected_records):
        assert record.chrom == "1"
        assert record.start == expected_record[0]
        assert record.score == expected_record[1]
        assert record.fields[8] == expected_record[2]


EXPECTED_BED_FILE = """1\t2\t3\t4\t5\t6
7\t8\t9\t10\t11\t12
"""


def test_create_temp_file_from_records(bedtools_service):
    path = bedtools_service.create_temp_file_from_records(
        [
            (7, 8, 9, 10, 11, 12),
            (1, 2, 3, 4, 5, 6),
        ]
    )
    with open(path) as fp:
        assert fp.read() == EXPECTED_BED_FILE


EXPECTED_EUF_FILE = """1\t0\t1\tname\t0\t.\t0\t1\t0,0,0\t10\t5
"""


def test_create_temp_euf_file(bedtools_service):
    path = bedtools_service.create_temp_euf_file(
        [
            EufRecord(
                chrom="1",
                start=0,
                end=1,
                name="name",
                score=0,
                strand=".",
                thick_start=0,
                thick_end=1,
                item_rgb="0,0,0",
                coverage=10,
                frequency=5,
            ),
        ]
    )
    with open(path) as fp:
        assert fp.read() == EXPECTED_EUF_FILE


@pytest.mark.parametrize(
    "feature",
    ["intron", "intergenic"],
)
def test_check_features(feature, bedtools_service):
    features = {k: list(v.keys()) for k, v in FEATURES.items()}
    assert (
        bedtools_service._check_feature(feature, features, "parent")
        == f"parent/{feature}.bed"
    )
