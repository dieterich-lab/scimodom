import pytest

from scimodom.services.bedtools import BedToolsService
from scimodom.utils.bedtools_dto import (
    ModificationRecord,
    Strand,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
)


@pytest.fixture
def bedtools_service(tmpdir):
    yield BedToolsService(tmp_path=tmpdir)


def test_get_modification_from_bedtools_data():
    record = BedToolsService._get_modification_from_bedtools_data(
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
    assert isinstance(record, ModificationRecord)
    assert record.chrom == "1"
    assert record.start == 1043431
    assert record.end == 1043432
    assert record.name == "Y"
    assert record.score == 190
    assert record.strand == Strand.FORWARD
    assert record.dataset_id == "iMuwPsi24Yka"
    assert record.coverage == 576
    assert record.frequency == 19


DATASET_A = [
    ModificationRecord(
        chrom="1",
        start=101,
        end=102,
        name="m6A",
        score=1,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        dataset_id="DATASET_A___",
    ),
    ModificationRecord(
        chrom="1",
        start=199,
        end=200,
        name="m6A",
        score=2,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        dataset_id="DATASET_A___",
    ),
    ModificationRecord(
        chrom="1",
        start=200,
        end=201,
        name="m6A",
        score=3,
        strand=Strand.FORWARD,
        coverage=50,
        frequency=60,
        dataset_id="DATASET_A___",
    ),
    ModificationRecord(
        chrom="1",
        start=299,
        end=300,
        name="m6A",
        score=4,
        strand=Strand.REVERSE,
        coverage=70,
        frequency=80,
        dataset_id="DATASET_A___",
    ),
    ModificationRecord(
        chrom="1",
        start=599,
        end=600,
        name="m6A",
        score=5,
        strand=Strand.FORWARD,
        coverage=90,
        frequency=100,
        dataset_id="DATASET_A___",
    ),
]
DATASET_B = [
    ModificationRecord(
        chrom="1",
        start=1,
        end=2,
        name="m6A",
        score=6,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        dataset_id="DATASET_B___",
    ),
    ModificationRecord(
        chrom="1",
        start=199,
        end=200,
        name="m6A",
        score=7,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        dataset_id="DATASET_B___",
    ),
    ModificationRecord(
        chrom="1",
        start=299,
        end=300,
        name="m6A",
        score=8,
        strand=Strand.FORWARD,
        coverage=50,
        frequency=60,
        dataset_id="DATASET_B___",
    ),
]
DATASET_C = [
    ModificationRecord(
        chrom="1",
        start=97,
        end=102,
        name="m6A",
        score=9,
        strand=Strand.FORWARD,
        coverage=10,
        frequency=20,
        dataset_id="DATASET_C___",
    ),
    ModificationRecord(
        chrom="1",
        start=197,
        end=202,
        name="m6A",
        score=10,
        strand=Strand.FORWARD,
        coverage=30,
        frequency=40,
        dataset_id="DATASET_C___",
    ),
    ModificationRecord(
        chrom="1",
        start=295,
        end=300,
        name="m6A",
        score=11,
        strand=Strand.REVERSE,
        coverage=50,
        frequency=60,
        dataset_id="DATASET_C___",
    ),
    ModificationRecord(
        chrom="1",
        start=1,
        end=6,
        name="m6A",
        score=12,
        strand=Strand.FORWARD,
        coverage=70,
        frequency=80,
        dataset_id="DATASET_C___",
    ),
]


EXPECTED_RESULT_INTERSECT_A_WITH_BC = [
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ModificationRecord(
            chrom="1",
            start=97,
            end=102,
            name="m6A",
            score=9,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=10,
            frequency=20,
        ),
    ),
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ModificationRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ModificationRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
    ),
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=4,
            strand=Strand.REVERSE,
            dataset_id="DATASET_A___",
            coverage=70,
            frequency=80,
        ),
        b=ModificationRecord(
            chrom="1",
            start=295,
            end=300,
            name="m6A",
            score=11,
            strand=Strand.REVERSE,
            dataset_id="DATASET_C___",
            coverage=50,
            frequency=60,
        ),
    ),
]


def test_intersect(bedtools_service):
    result = list(
        bedtools_service.intersect(DATASET_A, [DATASET_B, DATASET_C], is_strand=True)
    )
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_BC


EXPECTED_RESULT_CLOSEST_A_WITH_BC = [
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ModificationRecord(
            chrom="1",
            start=1,
            end=6,
            name="m6A",
            score=12,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=70,
            frequency=80,
        ),
        distance=-96,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ModificationRecord(
            chrom="1",
            start=197,
            end=202,
            name="m6A",
            score=10,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=30,
            frequency=40,
        ),
        distance=96,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ModificationRecord(
            chrom="1",
            start=97,
            end=102,
            name="m6A",
            score=9,
            strand=Strand.FORWARD,
            dataset_id="DATASET_C___",
            coverage=10,
            frequency=20,
        ),
        distance=-98,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=-1,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=599,
            end=600,
            name="m6A",
            score=5,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=90,
            frequency=100,
        ),
        b=ModificationRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=-300,
    ),
]


def test_closest(bedtools_service):
    result = list(
        bedtools_service.closest(DATASET_A, [DATASET_B, DATASET_C], is_strand=True)
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
        dataset_id="DATASET_A___",
        coverage=90,
        frequency=100,
    ),
]


def test_subtract(bedtools_service):
    result = list(
        bedtools_service.subtract(DATASET_A, [DATASET_B, DATASET_C], is_strand=True)
    )
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_BC


EXPECTED_RESULT_INTERSECT_A_WITH_B = [
    IntersectRecord(
        a=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
    ),
]


def test_intersect_simple(bedtools_service):
    result = list(bedtools_service.intersect(DATASET_A, [DATASET_B], is_strand=True))
    assert result == EXPECTED_RESULT_INTERSECT_A_WITH_B


EXPECTED_RESULT_CLOSEST_A_WITH_B = [
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=101,
            end=102,
            name="m6A",
            score=1,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=10,
            frequency=20,
        ),
        b=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=98,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=2,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=30,
            frequency=40,
        ),
        b=ModificationRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=100,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=200,
            end=201,
            name="m6A",
            score=3,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=50,
            frequency=60,
        ),
        b=ModificationRecord(
            chrom="1",
            start=199,
            end=200,
            name="m6A",
            score=7,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=30,
            frequency=40,
        ),
        distance=-1,
    ),
    ClosestRecord(
        a=ModificationRecord(
            chrom="1",
            start=599,
            end=600,
            name="m6A",
            score=5,
            strand=Strand.FORWARD,
            dataset_id="DATASET_A___",
            coverage=90,
            frequency=100,
        ),
        b=ModificationRecord(
            chrom="1",
            start=299,
            end=300,
            name="m6A",
            score=8,
            strand=Strand.FORWARD,
            dataset_id="DATASET_B___",
            coverage=50,
            frequency=60,
        ),
        distance=-300,
    ),
]


def test_closest_simple(bedtools_service):
    result = list(bedtools_service.closest(DATASET_A, [DATASET_B], is_strand=True))
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
        dataset_id="DATASET_A___",
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
        dataset_id="DATASET_A___",
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
        dataset_id="DATASET_A___",
    ),
    SubtractRecord(
        chrom="1",
        start=599,
        end=600,
        name="m6A",
        score=5,
        strand=Strand.FORWARD,
        dataset_id="DATASET_A___",
        coverage=90,
        frequency=100,
    ),
]


def test_subtract_simple(bedtools_service):
    result = list(bedtools_service.subtract(DATASET_A, [DATASET_B], is_strand=True))
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_B


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
