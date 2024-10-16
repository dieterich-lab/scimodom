from io import StringIO
import pytest

from scimodom.services.bedtools import BedToolsService
from scimodom.utils.bedtools_dto import (
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

# tests


def test_intersect_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.intersect_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_B


def test_closest_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.closest_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_CLOSEST_A_WITH_B


def test_subtract_comparison_records_simple(bedtools_service):
    result = list(
        bedtools_service.subtract_comparison_records(
            DATASET_A, [DATASET_B], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_B


def test_intersect_comparison_records(bedtools_service):
    result = list(
        bedtools_service.intersect_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_BC


def test_closest_comparison_records(bedtools_service):
    result = list(
        bedtools_service.closest_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_CLOSEST_A_WITH_BC


def test_subtract_comparison_records(bedtools_service):
    result = list(
        bedtools_service.subtract_comparison_records(
            DATASET_A, [DATASET_B, DATASET_C], is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_BC


def test_intersect_bed6_records(bedtools_service):
    result = list(
        bedtools_service.intersect_bed6_records(
            RECORDS_A, StringIO(BED_FILE), is_strand=True
        )
    )
    assert result == EXPECTED_RESULT_INTERSECT_BED6_A_WITH_B
