from io import StringIO
import pytest

from pybedtools import BedTool

from scimodom.services.bedtools import BedToolsService
from scimodom.utils.bedtools_dto import (
    EufRecord,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
    ComparisonRecord,
    Bed6Record,
)
from scimodom.utils.common_dto import Strand


@pytest.fixture
def bedtools_service(tmp_path):
    yield BedToolsService(tmp_path=tmp_path)


DATASET_A = [
    ComparisonRecord(
        chrom="1",
        start=101,
        end=102,
        name="m6A",
        score=1,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        eufid="DATASET_A___",
    ),
    ComparisonRecord(
        chrom="1",
        start=199,
        end=200,
        name="m6A",
        score=2,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        eufid="DATASET_A___",
    ),
    ComparisonRecord(
        chrom="1",
        start=200,
        end=201,
        name="m6A",
        score=3,
        strand=Strand.FORWARD,
        coverage=50,
        frequency=60,
        eufid="DATASET_A___",
    ),
    ComparisonRecord(
        chrom="1",
        start=299,
        end=300,
        name="m6A",
        score=4,
        strand=Strand.REVERSE,
        coverage=70,
        frequency=80,
        eufid="DATASET_A___",
    ),
    ComparisonRecord(
        chrom="1",
        start=599,
        end=600,
        name="m6A",
        score=5,
        strand=Strand.FORWARD,
        coverage=90,
        frequency=100,
        eufid="DATASET_A___",
    ),
]
DATASET_B = [
    ComparisonRecord(
        chrom="1",
        start=1,
        end=2,
        name="m6A",
        score=6,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        eufid="DATASET_B___",
    ),
    ComparisonRecord(
        chrom="1",
        start=199,
        end=200,
        name="m6A",
        score=7,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        eufid="DATASET_B___",
    ),
    ComparisonRecord(
        chrom="1",
        start=299,
        end=300,
        name="m6A",
        score=8,
        strand=Strand.FORWARD,
        coverage=50,
        frequency=60,
        eufid="DATASET_B___",
    ),
]
DATASET_C = [
    ComparisonRecord(
        chrom="1",
        start=97,
        end=102,
        name="m6A",
        score=9,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        eufid="DATASET_C___",
    ),
    ComparisonRecord(
        chrom="1",
        start=197,
        end=202,
        name="m6A",
        score=10,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        eufid="DATASET_C___",
    ),
    ComparisonRecord(
        chrom="1",
        start=295,
        end=300,
        name="m6A",
        score=11,
        strand=Strand.REVERSE,
        coverage=50,
        frequency=60,
        eufid="DATASET_C___",
    ),
    ComparisonRecord(
        chrom="1",
        start=1,
        end=6,
        name="m6A",
        score=12,
        strand=Strand.FORWARD,
        coverage=70,
        frequency=80,
        eufid="DATASET_C___",
    ),
]


EXPECTED_RESULT_INTERSECT_A_WITH_BC = [
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=97,
            end=102,
            name="m6A",
            score=9,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=10,
            frequency=20,
        ),
    ),
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=4,
            strand=Strand.REVERSE,
            eufid="DATASET_A___",
            coverage=70,
            frequency=80,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=295,
            end=300,
            name="m6A",
            score=11,
            strand=Strand.REVERSE,
            eufid="DATASET_C___",
            coverage=50,
            frequency=60,
        ),
    ),
]


def test_intersect_comparison_records(bedtools_service):
    result = list(
        bedtools_service.intersect_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_BC


EXPECTED_RESULT_CLOSEST_A_WITH_BC = [
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=1,
            end=6,
            name="m6A",
            score=12,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=70,
            frequency=80,
        ),
        distance=-96,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
        distance=96,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=97,
            end=102,
            name="m6A",
            score=9,
            strand=Strand.FORWARD,
            eufid="DATASET_C___",
            coverage=10,
            frequency=20,
        ),
        distance=-98,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=-1,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=599,
            end=600,
            name="m6A",
            score=5,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=90,
            frequency=100,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=-300,
    ),
]


def test_closest_comparison_records(bedtools_service):
    result = list(
        bedtools_service.closest_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_CLOSEST_A_WITH_BC


EXPECTED_RESULT_SUBTRACT_A_WITH_BC = [
    SubtractRecord(
        chrom="1",
        start=599,
        end=600,
        name="m6A",
        score=5,
        strand=Strand.FORWARD,
        eufid="DATASET_A___",
        coverage=90,
        frequency=100,
    ),
]


def test_subtract_comparison_records(bedtools_service):
    result = list(
        bedtools_service.subtract_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_BC


EXPECTED_RESULT_INTERSECT_A_WITH_B = [
    IntersectRecord(
        a=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
    ),
]


def test_intersect_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.intersect_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_B


EXPECTED_RESULT_CLOSEST_A_WITH_B = [
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=98,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=100,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=-1,
    ),
    ClosestRecord(
        a=ComparisonRecord(
            chrom="1",
            start=599,
            end=600,
            name="m6A",
            score=5,
            strand=Strand.FORWARD,
            eufid="DATASET_A___",
            coverage=90,
            frequency=100,
        ),
        b=ComparisonRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            eufid="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=-300,
    ),
]


def test_closest_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.closest_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_CLOSEST_A_WITH_B


EXPECTED_RESULT_SUBTRACT_A_WITH_B = [
    SubtractRecord(
        chrom="1",
        start=101,
        end=102,
        name="m6A",
        score=1,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        eufid="DATASET_A___",
    ),
    SubtractRecord(
        chrom="1",
        start=200,
        end=201,
        name="m6A",
        score=3,
        strand=Strand.FORWARD,
        coverage=50,
        frequency=60,
        eufid="DATASET_A___",
    ),
    SubtractRecord(
        chrom="1",
        start=299,
        end=300,
        name="m6A",
        score=4,
        strand=Strand.REVERSE,
        coverage=70,
        frequency=80,
        eufid="DATASET_A___",
    ),
    SubtractRecord(
        chrom="1",
        start=599,
        end=600,
        name="m6A",
        score=5,
        strand=Strand.FORWARD,
        eufid="DATASET_A___",
        coverage=90,
        frequency=100,
    ),
]


def test_subtract_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.subtract_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_B


RECORDS_A = [
    Bed6Record(
        chrom="1",
        start=101,
        end=102,
        name="m6A",
        score=1,
        strand=Strand.FORWARD,
    ),
    Bed6Record(
        chrom="1",
        start=199,
        end=200,
        name="m6A",
        score=2,
        strand=Strand.FORWARD,
    ),
]
BED_FILE = """1\t100\t108\t4\t5\t+\t7\t8\t9\t10\t11\t12
1\t195\t202\t4\t5\t-\t7\t8\t9\t10\t11\t12"""
EXPECTED_RESULT_INTERSECT_BED6_A_WITH_B = [
    Bed6Record(
        chrom="1",
        start=100,
        end=108,
        name="4",
        score=5,
        strand=Strand.FORWARD,
    ),
]


def test_intersect_bed6_records(bedtools_service):
    result = list(
        bedtools_service.intersect_bed6_records(
            RECORDS_A, StringIO(BED_FILE), is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_BED6_A_WITH_B


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
