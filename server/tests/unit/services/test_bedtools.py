from scimodom.services.bedtools import BedToolsService
from scimodom.utils.bedtools_dto import (
    ModificationRecord,
    Strand,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
)


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


# def _get_expected_records(repeat=False):
#     a = [
#         ("1", 101, 102, "m6A", 1, Strand.FORWARD, "KEyK5s3pcKjE", 10, 20),
#         ("1", 199, 200, "m6A", 2, Strand.FORWARD, "KEyK5s3pcKjE", 30, 40),
#         ("1", 200, 201, "m6A", 3, Strand.FORWARD, "KEyK5s3pcKjE", 50, 60),
#         ("1", 299, 300, "m6A", 4, Strand.REVERSE, "KEyK5s3pcKjE", 70, 80),
#         ("1", 599, 600, "m6A", 5, Strand.FORWARD, "KEyK5s3pcKjE", 90, 100),
#     ]
#     if repeat:
#         a.extend(
#             [
#                 ("1", 101, 102, "m6A", 1, Strand.FORWARD, "8sQjh8xwioFr", 10, 20),
#                 ("1", 199, 200, "m6A", 2, Strand.FORWARD, "8sQjh8xwioFr", 30, 40),
#                 ("1", 200, 201, "m6A", 3, Strand.FORWARD, "8sQjh8xwioFr", 50, 60),
#                 ("1", 299, 300, "m6A", 4, Strand.REVERSE, "8sQjh8xwioFr", 70, 80),
#                 ("1", 599, 600, "m6A", 5, Strand.FORWARD, "8sQjh8xwioFr", 90, 100),
#             ]
#         )
#     b = [
#         ("1", 1, 2, "m6A", 6, Strand.FORWARD, "FCfhtbEJpbvR", 10, 20),
#         ("1", 199, 200, "m6A", 7, Strand.FORWARD, "FCfhtbEJpbvR", 30, 40),
#         ("1", 299, 300, "m6A", 8, Strand.FORWARD, "FCfhtbEJpbvR", 50, 60),
#     ]
#     c = [
#         ("1", 97, 102, "m6A", 9, Strand.FORWARD, "3HsmkimcHAFA", 10, 20),
#         ("1", 197, 202, "m6A", 10, Strand.FORWARD, "3HsmkimcHAFA", 30, 40),
#         ("1", 295, 300, "m6A", 11, Strand.REVERSE, "3HsmkimcHAFA", 50, 60),
#         ("1", 1, 6, "m6A", 12, Strand.FORWARD, "3HsmkimcHAFA", 70, 80),
#     ]
#     return a, b, c
#
#
# def _get_expected_results(operation):
#     intersect = [
#         {
#             "chrom": "1",
#             "start": 101,
#             "end": 102,
#             "name": "m6A",
#             "score": 1,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 10,
#             "frequency": 20,
#             "chrom_b": "1",
#             "start_b": 97,
#             "end_b": 102,
#             "name_b": "m6A",
#             "score_b": 9,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 10,
#             "frequency_b": 20,
#         },
#         {
#             "chrom": "1",
#             "start": 199,
#             "end": 200,
#             "name": "m6A",
#             "score": 2,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 30,
#             "frequency": 40,
#             "chrom_b": "1",
#             "start_b": 199,
#             "end_b": 200,
#             "name_b": "m6A",
#             "score_b": 7,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 30,
#             "frequency_b": 40,
#         },
#         {
#             "chrom": "1",
#             "start": 199,
#             "end": 200,
#             "name": "m6A",
#             "score": 2,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 30,
#             "frequency": 40,
#             "chrom_b": "1",
#             "start_b": 197,
#             "end_b": 202,
#             "name_b": "m6A",
#             "score_b": 10,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 30,
#             "frequency_b": 40,
#         },
#         {
#             "chrom": "1",
#             "start": 200,
#             "end": 201,
#             "name": "m6A",
#             "score": 3,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 50,
#             "frequency": 60,
#             "chrom_b": "1",
#             "start_b": 197,
#             "end_b": 202,
#             "name_b": "m6A",
#             "score_b": 10,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 30,
#             "frequency_b": 40,
#         },
#         {
#             "chrom": "1",
#             "start": 299,
#             "end": 300,
#             "name": "m6A",
#             "score": 4,
#             "strand": Strand.REVERSE,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 70,
#             "frequency": 80,
#             "chrom_b": "1",
#             "start_b": 295,
#             "end_b": 300,
#             "name_b": "m6A",
#             "score_b": 11,
#             "strand_b": Strand.REVERSE,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 50,
#             "frequency_b": 60,
#         },
#     ]
#     closest = [
#         {
#             "chrom": "1",
#             "start": 101,
#             "end": 102,
#             "name": "m6A",
#             "score": 1,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 10,
#             "frequency": 20,
#             "chrom_b": "1",
#             "start_b": 1,
#             "end_b": 6,
#             "name_b": "m6A",
#             "score_b": 12,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 70,
#             "frequency_b": 80,
#             "distance": -96,
#         },
#         {
#             "chrom": "1",
#             "start": 101,
#             "end": 102,
#             "name": "m6A",
#             "score": 1,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 10,
#             "frequency": 20,
#             "chrom_b": "1",
#             "start_b": 197,
#             "end_b": 202,
#             "name_b": "m6A",
#             "score_b": 10,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 30,
#             "frequency_b": 40,
#             "distance": 96,
#         },
#         {
#             "chrom": "1",
#             "start": 199,
#             "end": 200,
#             "name": "m6A",
#             "score": 2,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 30,
#             "frequency": 40,
#             "chrom_b": "1",
#             "start_b": 97,
#             "end_b": 102,
#             "name_b": "m6A",
#             "score_b": 9,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "3HsmkimcHAFA",
#             "coverage_b": 10,
#             "frequency_b": 20,
#             "distance": -98,
#         },
#         {
#             "chrom": "1",
#             "start": 200,
#             "end": 201,
#             "name": "m6A",
#             "score": 3,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 50,
#             "frequency": 60,
#             "chrom_b": "1",
#             "start_b": 199,
#             "end_b": 200,
#             "name_b": "m6A",
#             "score_b": 7,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 30,
#             "frequency_b": 40,
#             "distance": -1,
#         },
#         {
#             "chrom": "1",
#             "start": 599,
#             "end": 600,
#             "name": "m6A",
#             "score": 5,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 90,
#             "frequency": 100,
#             "chrom_b": "1",
#             "start_b": 299,
#             "end_b": 300,
#             "name_b": "m6A",
#             "score_b": 8,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 50,
#             "frequency_b": 60,
#             "distance": -300,
#         },
#     ]
#     subtract = [
#         {
#             "chrom": "1",
#             "start": 599,
#             "end": 600,
#             "name": "m6A",
#             "score": 5,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 90,
#             "frequency": 100,
#         }
#     ]
#
#     expected = (
#         intersect
#         if operation == "intersect"
#         else closest
#         if operation == "closest"
#         else subtract
#     )
#     return expected
#
#
# def _get_expected_results_simple(operation):
#     intersect = [
#         {
#             "chrom": "1",
#             "start": 199,
#             "end": 200,
#             "name": "m6A",
#             "score": 2,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 30,
#             "frequency": 40,
#             "chrom_b": "1",
#             "start_b": 199,
#             "end_b": 200,
#             "name_b": "m6A",
#             "score_b": 7,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 30,
#             "frequency_b": 40,
#         }
#     ]
#     closest = [
#         {
#             "chrom": "1",
#             "start": 101,
#             "end": 102,
#             "name": "m6A",
#             "score": 1,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 10,
#             "frequency": 20,
#             "chrom_b": "1",
#             "start_b": 199,
#             "end_b": 200,
#             "name_b": "m6A",
#             "score_b": 7,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 30,
#             "frequency_b": 40,
#             "distance": 98,
#         },
#         {
#             "chrom": "1",
#             "start": 199,
#             "end": 200,
#             "name": "m6A",
#             "score": 2,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 30,
#             "frequency": 40,
#             "chrom_b": "1",
#             "start_b": 299,
#             "end_b": 300,
#             "name_b": "m6A",
#             "score_b": 8,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 50,
#             "frequency_b": 60,
#             "distance": 100,
#         },
#         {
#             "chrom": "1",
#             "start": 200,
#             "end": 201,
#             "name": "m6A",
#             "score": 3,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 50,
#             "frequency": 60,
#             "chrom_b": "1",
#             "start_b": 199,
#             "end_b": 200,
#             "name_b": "m6A",
#             "score_b": 7,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 30,
#             "frequency_b": 40,
#             "distance": -1,
#         },
#         {
#             "chrom": "1",
#             "start": 599,
#             "end": 600,
#             "name": "m6A",
#             "score": 5,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 90,
#             "frequency": 100,
#             "chrom_b": "1",
#             "start_b": 299,
#             "end_b": 300,
#             "name_b": "m6A",
#             "score_b": 8,
#             "strand_b": Strand.FORWARD,
#             "dataset_id_b": "FCfhtbEJpbvR",
#             "coverage_b": 50,
#             "frequency_b": 60,
#             "distance": -300,
#         },
#     ]
#     subtract = [
#         {
#             "chrom": "1",
#             "start": 101,
#             "end": 102,
#             "name": "m6A",
#             "score": 1,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 10,
#             "frequency": 20,
#         },
#         {
#             "chrom": "1",
#             "start": 200,
#             "end": 201,
#             "name": "m6A",
#             "score": 3,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 50,
#             "frequency": 60,
#         },
#         {
#             "chrom": "1",
#             "start": 299,
#             "end": 300,
#             "name": "m6A",
#             "score": 4,
#             "strand": Strand.REVERSE,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 70,
#             "frequency": 80,
#         },
#         {
#             "chrom": "1",
#             "start": 599,
#             "end": 600,
#             "name": "m6A",
#             "score": 5,
#             "strand": Strand.FORWARD,
#             "dataset_id": "KEyK5s3pcKjE",
#             "coverage": 90,
#             "frequency": 100,
#         },
#     ]
#
#     expected = (
#         intersect
#         if operation == "intersect"
#         else closest
#         if operation == "closest"
#         else subtract
#     )
#     return expected


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


def test_intersect(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.intersect(DATASET_A, [DATASET_B, DATASET_C], is_strand=True))
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


def test_closest(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.closest(DATASET_A, [DATASET_B, DATASET_C], is_strand=True))
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


def test_subtract(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.subtract(DATASET_A, [DATASET_B, DATASET_C], is_strand=True))
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


def test_intersect_simple(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.intersect(DATASET_A, [DATASET_B], is_strand=True))
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


def test_closest_simple(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.closest(DATASET_A, [DATASET_B], is_strand=True))
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


def test_subtract_simple(tmpdir):
    service = BedToolsService(tempdir=tmpdir)
    result = list(service.subtract(DATASET_A, [DATASET_B], is_strand=True))
    assert result == EXPECTED_RESULT_SUBTRACT_A_WITH_B
