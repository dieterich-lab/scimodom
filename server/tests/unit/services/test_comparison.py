from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from scimodom.services.comparison import ComparisonService
from scimodom.database.models import (
    Association,
    Selection,
    Dataset,
    Data,
    Project,
    ProjectContact,
)


def _get_data():
    a = [
        ("1", 101, 102, "m6A", 1, "+", 101, 102, "0,0,0", 10, 20),
        ("1", 199, 200, "m6A", 2, "+", 199, 200, "0,0,0", 30, 40),
        ("1", 200, 201, "m6A", 3, "+", 200, 201, "0,0,0", 50, 60),
        ("1", 299, 300, "m6A", 4, "-", 299, 300, "0,0,0", 70, 80),
        ("1", 599, 600, "m6A", 5, "+", 599, 600, "0,0,0", 90, 100),
    ]
    b = [
        ("1", 1, 2, "m6A", 6, "+", 1, 2, "0,0,0", 10, 20),
        ("1", 199, 200, "m6A", 7, "+", 199, 200, "0,0,0", 30, 40),
        ("1", 299, 300, "m6A", 8, "+", 299, 300, "0,0,0", 50, 60),
    ]
    c = [
        ("1", 97, 102, "m6A", 9, "+", 97, 102, "0,0,0", 10, 20),
        ("1", 197, 202, "m6A", 10, "+", 197, 202, "0,0,0", 30, 40),
        ("1", 295, 300, "m6A", 11, "-", 295, 300, "0,0,0", 50, 60),
        ("1", 1, 6, "m6A", 12, "+", 1, 6, "0,0,0", 70, 80),
    ]
    return a, b, c


def _get_expected_records(repeat=False):
    a = [
        ("1", 101, 102, "m6A", 1, "+", "KEyK5s3pcKjE", 10, 20),
        ("1", 199, 200, "m6A", 2, "+", "KEyK5s3pcKjE", 30, 40),
        ("1", 200, 201, "m6A", 3, "+", "KEyK5s3pcKjE", 50, 60),
        ("1", 299, 300, "m6A", 4, "-", "KEyK5s3pcKjE", 70, 80),
        ("1", 599, 600, "m6A", 5, "+", "KEyK5s3pcKjE", 90, 100),
    ]
    if repeat:
        a.extend(
            [
                ("1", 101, 102, "m6A", 1, "+", "8sQjh8xwioFr", 10, 20),
                ("1", 199, 200, "m6A", 2, "+", "8sQjh8xwioFr", 30, 40),
                ("1", 200, 201, "m6A", 3, "+", "8sQjh8xwioFr", 50, 60),
                ("1", 299, 300, "m6A", 4, "-", "8sQjh8xwioFr", 70, 80),
                ("1", 599, 600, "m6A", 5, "+", "8sQjh8xwioFr", 90, 100),
            ]
        )
    b = [
        ("1", 1, 2, "m6A", 6, "+", "FCfhtbEJpbvR", 10, 20),
        ("1", 199, 200, "m6A", 7, "+", "FCfhtbEJpbvR", 30, 40),
        ("1", 299, 300, "m6A", 8, "+", "FCfhtbEJpbvR", 50, 60),
    ]
    c = [
        ("1", 97, 102, "m6A", 9, "+", "3HsmkimcHAFA", 10, 20),
        ("1", 197, 202, "m6A", 10, "+", "3HsmkimcHAFA", 30, 40),
        ("1", 295, 300, "m6A", 11, "-", "3HsmkimcHAFA", 50, 60),
        ("1", 1, 6, "m6A", 12, "+", "3HsmkimcHAFA", 70, 80),
    ]
    return a, b, c


def _get_expected_results(operation):
    intersect = [
        {
            "chrom": "1",
            "start": 101,
            "end": 102,
            "name": "m6A",
            "score": 1,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 10,
            "frequency": 20,
            "chrom_b": "1",
            "start_b": 97,
            "end_b": 102,
            "name_b": "m6A",
            "score_b": 9,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 10,
            "frequency_b": 20,
        },
        {
            "chrom": "1",
            "start": 199,
            "end": 200,
            "name": "m6A",
            "score": 2,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 30,
            "frequency": 40,
            "chrom_b": "1",
            "start_b": 199,
            "end_b": 200,
            "name_b": "m6A",
            "score_b": 7,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 30,
            "frequency_b": 40,
        },
        {
            "chrom": "1",
            "start": 199,
            "end": 200,
            "name": "m6A",
            "score": 2,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 30,
            "frequency": 40,
            "chrom_b": "1",
            "start_b": 197,
            "end_b": 202,
            "name_b": "m6A",
            "score_b": 10,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 30,
            "frequency_b": 40,
        },
        {
            "chrom": "1",
            "start": 200,
            "end": 201,
            "name": "m6A",
            "score": 3,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 50,
            "frequency": 60,
            "chrom_b": "1",
            "start_b": 197,
            "end_b": 202,
            "name_b": "m6A",
            "score_b": 10,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 30,
            "frequency_b": 40,
        },
        {
            "chrom": "1",
            "start": 299,
            "end": 300,
            "name": "m6A",
            "score": 4,
            "strand": "-",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 70,
            "frequency": 80,
            "chrom_b": "1",
            "start_b": 295,
            "end_b": 300,
            "name_b": "m6A",
            "score_b": 11,
            "strand_b": "-",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 50,
            "frequency_b": 60,
        },
    ]
    closest = [
        {
            "chrom": "1",
            "start": 101,
            "end": 102,
            "name": "m6A",
            "score": 1,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 10,
            "frequency": 20,
            "chrom_b": "1",
            "start_b": 1,
            "end_b": 6,
            "name_b": "m6A",
            "score_b": 12,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 70,
            "frequency_b": 80,
            "distance": -96,
        },
        {
            "chrom": "1",
            "start": 101,
            "end": 102,
            "name": "m6A",
            "score": 1,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 10,
            "frequency": 20,
            "chrom_b": "1",
            "start_b": 197,
            "end_b": 202,
            "name_b": "m6A",
            "score_b": 10,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 30,
            "frequency_b": 40,
            "distance": 96,
        },
        {
            "chrom": "1",
            "start": 199,
            "end": 200,
            "name": "m6A",
            "score": 2,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 30,
            "frequency": 40,
            "chrom_b": "1",
            "start_b": 97,
            "end_b": 102,
            "name_b": "m6A",
            "score_b": 9,
            "strand_b": "+",
            "dataset_id_b": "3HsmkimcHAFA",
            "coverage_b": 10,
            "frequency_b": 20,
            "distance": -98,
        },
        {
            "chrom": "1",
            "start": 200,
            "end": 201,
            "name": "m6A",
            "score": 3,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 50,
            "frequency": 60,
            "chrom_b": "1",
            "start_b": 199,
            "end_b": 200,
            "name_b": "m6A",
            "score_b": 7,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 30,
            "frequency_b": 40,
            "distance": -1,
        },
        {
            "chrom": "1",
            "start": 599,
            "end": 600,
            "name": "m6A",
            "score": 5,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 90,
            "frequency": 100,
            "chrom_b": "1",
            "start_b": 299,
            "end_b": 300,
            "name_b": "m6A",
            "score_b": 8,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 50,
            "frequency_b": 60,
            "distance": -300,
        },
    ]
    subtract = [
        {
            "chrom": "1",
            "start": 599,
            "end": 600,
            "name": "m6A",
            "score": 5,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 90,
            "frequency": 100,
        }
    ]

    expected = (
        intersect
        if operation == "intersect"
        else closest
        if operation == "closest"
        else subtract
    )
    return expected


def _get_expected_results_simple(operation):
    intersect = [
        {
            "chrom": "1",
            "start": 199,
            "end": 200,
            "name": "m6A",
            "score": 2,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 30,
            "frequency": 40,
            "chrom_b": "1",
            "start_b": 199,
            "end_b": 200,
            "name_b": "m6A",
            "score_b": 7,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 30,
            "frequency_b": 40,
        }
    ]
    closest = [
        {
            "chrom": "1",
            "start": 101,
            "end": 102,
            "name": "m6A",
            "score": 1,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 10,
            "frequency": 20,
            "chrom_b": "1",
            "start_b": 199,
            "end_b": 200,
            "name_b": "m6A",
            "score_b": 7,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 30,
            "frequency_b": 40,
            "distance": 98,
        },
        {
            "chrom": "1",
            "start": 199,
            "end": 200,
            "name": "m6A",
            "score": 2,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 30,
            "frequency": 40,
            "chrom_b": "1",
            "start_b": 299,
            "end_b": 300,
            "name_b": "m6A",
            "score_b": 8,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 50,
            "frequency_b": 60,
            "distance": 100,
        },
        {
            "chrom": "1",
            "start": 200,
            "end": 201,
            "name": "m6A",
            "score": 3,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 50,
            "frequency": 60,
            "chrom_b": "1",
            "start_b": 199,
            "end_b": 200,
            "name_b": "m6A",
            "score_b": 7,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 30,
            "frequency_b": 40,
            "distance": -1,
        },
        {
            "chrom": "1",
            "start": 599,
            "end": 600,
            "name": "m6A",
            "score": 5,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 90,
            "frequency": 100,
            "chrom_b": "1",
            "start_b": 299,
            "end_b": 300,
            "name_b": "m6A",
            "score_b": 8,
            "strand_b": "+",
            "dataset_id_b": "FCfhtbEJpbvR",
            "coverage_b": 50,
            "frequency_b": 60,
            "distance": -300,
        },
    ]
    subtract = [
        {
            "chrom": "1",
            "start": 101,
            "end": 102,
            "name": "m6A",
            "score": 1,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 10,
            "frequency": 20,
        },
        {
            "chrom": "1",
            "start": 200,
            "end": 201,
            "name": "m6A",
            "score": 3,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 50,
            "frequency": 60,
        },
        {
            "chrom": "1",
            "start": 299,
            "end": 300,
            "name": "m6A",
            "score": 4,
            "strand": "-",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 70,
            "frequency": 80,
        },
        {
            "chrom": "1",
            "start": 599,
            "end": 600,
            "name": "m6A",
            "score": 5,
            "strand": "+",
            "dataset_id": "KEyK5s3pcKjE",
            "coverage": 90,
            "frequency": 100,
        },
    ]

    expected = (
        intersect
        if operation == "intersect"
        else closest
        if operation == "closest"
        else subtract
    )
    return expected


def test_query_one_reference(Session, setup):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add(dataset)
        session.flush()
        eufid = dataset.id
        association = Association(dataset_id=eufid, selection_id=selection_id)
        session.add(association)
        session.flush()
        association_id = association.id

        rows, _, _ = _get_data()
        data = [
            Data(
                association_id=association_id,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
        ]
        session.add_all(data)
        session.commit()

        comparison_service = ComparisonService(session=Session())
        comparison_service.query_reference_records([eufid])
        expected_records, _, _ = _get_expected_records()
        assert comparison_service._reference_records == expected_records


def test_query_two_reference(Session, setup):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset1 = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        dataset2 = Dataset(
            id="8sQjh8xwioFr",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add_all([dataset1, dataset2])
        session.flush()
        eufid1 = dataset1.id
        eufid2 = dataset2.id
        association1 = Association(dataset_id=eufid1, selection_id=selection_id)
        association2 = Association(dataset_id=eufid2, selection_id=selection_id)
        session.add_all([association1, association2])
        session.flush()
        association_id1 = association1.id
        association_id2 = association2.id

        rows, _, _ = _get_data()
        data = [
            Data(
                association_id=association_id1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
        ]
        data.extend(
            Data(
                association_id=association_id2,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows
        )
        session.add_all(data)
        session.commit()

        comparison_service = ComparisonService(session=Session())
        comparison_service.query_reference_records([eufid1, eufid2])

        # order is not guaranteed
        expected_records, _, _ = _get_expected_records(repeat=True)
        assert set(comparison_service._reference_records) == set(expected_records)


def test_query_comparison(Session, setup):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset1 = Dataset(
            id="FCfhtbEJpbvR",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        dataset2 = Dataset(
            id="3HsmkimcHAFA",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add_all([dataset1, dataset2])
        session.flush()
        eufid1 = dataset1.id
        eufid2 = dataset2.id
        association1 = Association(dataset_id=eufid1, selection_id=selection_id)
        association2 = Association(dataset_id=eufid2, selection_id=selection_id)
        session.add_all([association1, association2])
        session.flush()
        association_id1 = association1.id
        association_id2 = association2.id

        _, rows1, rows2 = _get_data()
        data = [
            Data(
                association_id=association_id1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows1
        ]
        data.extend(
            Data(
                association_id=association_id2,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows2
        )
        session.add_all(data)
        session.commit()

        comparison_service = ComparisonService(session=Session())
        comparison_service.query_comparison_records([eufid1, eufid2])

        _, expected_records1, expected_records2 = _get_expected_records()
        assert len(comparison_service._comparison_records) == 2
        assert comparison_service._comparison_records[0] == expected_records1
        assert comparison_service._comparison_records[1] == expected_records2


@pytest.mark.parametrize(
    "is_euf",
    [(True), (False)],
)
def test_upload_bed(is_euf, Session, data_path):
    filen = Path(data_path.LOC, "test.bed")
    expected_records = [[("1", 0, 10, "m6A", 1000, "+", "Upload", 0, 0)]]
    if is_euf:
        expected_records = [[("1", 0, 10, "m6A", 1000, "+", "Upload", 10, 1)]]
    with Session() as session, session.begin():
        comparison_service = ComparisonService(session=Session())
        comparison_service.upload_records(filen, is_euf)
        comparison_service._comparison_records == expected_records


# test wrangling, type conversion, etc. but
# ... also relies on pybedtools' behaviour
# is_strand = True
@pytest.mark.parametrize(
    "operation",
    [
        ("intersect"),
        ("closest"),
        ("subtract"),
    ],
)
def test_operation(operation, Session, setup):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset1 = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        dataset2 = Dataset(
            id="FCfhtbEJpbvR",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        dataset3 = Dataset(
            id="3HsmkimcHAFA",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add_all([dataset1, dataset2, dataset3])
        session.flush()
        eufid1 = dataset1.id
        eufid2 = dataset2.id
        eufid3 = dataset3.id
        association1 = Association(dataset_id=eufid1, selection_id=selection_id)
        association2 = Association(dataset_id=eufid2, selection_id=selection_id)
        association3 = Association(dataset_id=eufid3, selection_id=selection_id)
        session.add_all([association1, association2, association3])
        session.flush()
        association_id1 = association1.id
        association_id2 = association2.id
        association_id3 = association3.id

        rows1, rows2, rows3 = _get_data()
        data = [
            Data(
                association_id=association_id1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows1
        ]
        data.extend(
            Data(
                association_id=association_id2,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows2
        )
        data.extend(
            Data(
                association_id=association_id3,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows3
        )
        session.add_all(data)
        session.commit()

        comparison_service = ComparisonService(session=Session())
        # is_strand = True
        comparison_service._init(operation, True)
        comparison_service.query_reference_records([eufid1])
        comparison_service.query_comparison_records([eufid2, eufid3])
        records = comparison_service.compare_dataset()
        expected_records = _get_expected_results(operation)
        assert records == expected_records


# same as above, but for one comparison dataset only
@pytest.mark.parametrize(
    "operation",
    [
        ("intersect"),
        ("closest"),
        ("subtract"),
    ],
)
def test_operation_simple(operation, Session, setup):
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    with Session() as session, session.begin():
        session.add_all(setup)
        selection = Selection(
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
        session.add(selection)
        session.flush()
        selection_id = selection.id
        contact = ProjectContact(
            contact_name="contact_name",
            contact_institution="contact_institution",
            contact_email="contact@email",
        )
        session.add(contact)
        session.flush()
        contact_id = contact.id
        project = Project(
            id="12345678",
            title="title",
            summary="summary",
            contact_id=contact_id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=stamp,
        )
        session.add(project)
        session.flush()
        smid = project.id
        dataset1 = Dataset(
            id="KEyK5s3pcKjE",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        dataset2 = Dataset(
            id="FCfhtbEJpbvR",
            project_id=smid,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        session.add_all([dataset1, dataset2])
        session.flush()
        eufid1 = dataset1.id
        eufid2 = dataset2.id
        association1 = Association(dataset_id=eufid1, selection_id=selection_id)
        association2 = Association(dataset_id=eufid2, selection_id=selection_id)
        session.add_all([association1, association2])
        session.flush()
        association_id1 = association1.id
        association_id2 = association2.id

        rows1, rows2, _ = _get_data()
        data = [
            Data(
                association_id=association_id1,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows1
        ]
        data.extend(
            Data(
                association_id=association_id2,
                chrom=chrom,
                start=start,
                end=end,
                name=name,
                score=score,
                strand=strand,
                thick_start=thick_start,
                thick_end=thick_end,
                item_rgb=item_rgb,
                coverage=coverage,
                frequency=frequency,
            )
            for chrom, start, end, name, score, strand, thick_start, thick_end, item_rgb, coverage, frequency in rows2
        )
        session.add_all(data)
        session.commit()

        comparison_service = ComparisonService(session=Session())
        # is_strand = True
        comparison_service._init(operation, True)
        comparison_service.query_reference_records([eufid1])
        comparison_service.query_comparison_records([eufid2])
        records = comparison_service.compare_dataset()
        expected_records = _get_expected_results_simple(operation)
        assert records == expected_records
