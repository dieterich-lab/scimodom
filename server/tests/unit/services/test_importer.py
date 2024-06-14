from io import StringIO
from pathlib import Path

import pytest
from sqlalchemy import func, select

from scimodom.database.models import Data, Dataset
from scimodom.services.importer import get_importer, get_bed_importer, get_buffer


# WHY WAS I ABLE TO ADD ASSOCIATION ID TO DATA IF THERE IS NO VALUE IN THE DB (FK)???
# IN FACT, NONE OF THESE TESTS USES setup... SO THE DB IS IN PRINCIPLE EMPTY...
# WHY IS THIS WORKING?


@pytest.mark.parametrize(
    "close_handle",
    [(True), (False)],
)
def test_importer(close_handle, Session, data_path):
    checkpoint = Session().begin_nested()
    try:
        importer = get_importer(
            filen=Path(data_path.LOC, "test.bed").as_posix(),
            organism_id=1,
            technology_id=1,
            smid="12345678",
            eufid="123456789ABC",
            title="title",
        )
        importer.header.parse_header()
        if close_handle:
            importer.header.close()
        importer.init_data_importer(association={"m6A": 1}, seqids=["1"])
        importer.data.parse_records()
    except:
        checkpoint.rollback()
        raise
    else:
        importer.data.close()

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Dataset)
        num_records = session.execute(stmt).scalar()
        records = session.execute(select(Dataset)).scalars().all()[0]
        assert num_records == 1
        assert records.id == "123456789ABC"
        assert records.organism_id == 1
        assert records.technology_id == 1
        assert records.project_id == "12345678"
        assert records.title == "title"
        assert records.modification_type == "RNA"
        assert records.sequencing_platform == "Sequencing platform"
        assert records.basecalling is None
        assert records.bioinformatics_workflow == "Workflow"
        assert records.experiment == "Description of experiment."
        assert records.external_source is None
        assert records.date_added.year == importer.header._stamp.year
        assert records.date_added.month == importer.header._stamp.month
        assert records.date_added.day == importer.header._stamp.day
        assert records.date_added.hour == importer.header._stamp.hour
        assert records.date_added.minute == importer.header._stamp.minute
        assert records.date_added.second == importer.header._stamp.second

        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        records = session.execute(select(Data)).scalars().all()[0]
        assert num_records == 1
        assert records.id == 1
        assert records.eufid == "123456789ABC"
        assert records.modification_id == 1
        assert records.chrom == "1"
        assert records.start == 0
        assert records.end == 10
        assert records.name == "m6A"
        assert records.score == 1000
        assert records.strand == "+"
        assert records.thick_start == 0
        assert records.thick_end == 10
        assert records.item_rgb == "0,0,0"
        assert records.coverage == 10
        assert records.frequency == 1


def test_importer_header_fail(Session, data_path):
    checkpoint = Session().begin_nested()
    try:
        importer = get_importer(
            filen=Path(data_path.LOC, "test_header_fail.bed").as_posix(),
            organism_id=1,
            technology_id=1,
            smid="12345678",
            eufid="123456789ABC",
            title="title",
        )
        importer.header.parse_header()
        importer.header.close()
        importer.init_data_importer(association={"m6A": 1}, seqids=["1"])
        importer.data.parse_records()
    except:
        checkpoint.rollback()
        # raise
    else:
        importer.data.close()

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Dataset)
        num_records = session.execute(stmt).scalar()
        assert num_records == 0
        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        assert num_records == 0


def test_importer_data_fail(Session, data_path):
    # This test does not actually fail! Data import is
    # pretty much fail-safe, most common problems are
    # excepted into a ValueError, and the line is skipped.
    # This allows in principle to read all "good" records
    # from a file that may be very badly formatted, e.g.
    # inconsistent number of columns, wrong delimiter, etc.
    # All "bad" records are discared, e.g. out of range
    # values, non-numerical values where a numerical value
    # is expected, etc.
    checkpoint = Session().begin_nested()
    try:
        importer = get_importer(
            filen=Path(data_path.LOC, "test_data_fail.bed").as_posix(),
            organism_id=1,
            technology_id=1,
            smid="12345678",
            eufid="123456789ABC",
            title="title",
        )
        importer.header.parse_header()
        importer.header.close()
        importer.init_data_importer(association={"m6A": 1}, seqids=["1"])
        importer.data.parse_records()
    except:
        checkpoint.rollback()
        # raise
    else:
        importer.data.close()

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Dataset)
        num_records = session.execute(stmt).scalar()
        records = session.execute(select(Dataset)).scalars().all()[0]
        assert num_records == 1
        assert records.id == "123456789ABC"
        assert records.organism_id == 1
        assert records.technology_id == 1
        assert records.project_id == "12345678"
        assert records.title == "title"
        assert records.modification_type == "RNA"
        assert records.sequencing_platform == "Sequencing platform"
        assert records.basecalling is None
        assert records.bioinformatics_workflow == "Workflow"
        assert records.experiment == "Description of experiment."
        assert records.external_source is None

        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        records = session.execute(select(Data)).scalars().all()
        assert num_records == 2
        for idx, record in enumerate(records):
            assert record.id == idx + 1
            assert record.eufid == "123456789ABC"
            assert record.modification_id == 1
            assert record.chrom == "1"
            assert record.start == 0
            assert record.end == 10
            assert record.name == "m6A"
            assert record.score == 1000
            assert record.strand == "+"
            assert record.thick_start == 0
            assert record.thick_end == 10
            assert record.item_rgb == "0,0,0"
            assert record.coverage == 10
            assert record.frequency == 1


def test_bed_importer(Session, data_path):
    # Test BED import. ValueError from BaseImporter are excepted
    # e.g. non-numerical value where numerical value is expected,
    # empty lines, wrong delimiter, more/less number of columns, etc.
    # We are not testing from wrong comment character (default to #),
    # but in principle this is also excepted by BaseImporter.
    # But BEDImporter does NOT validate values, e.g. chrom, strand,
    # or name can be anything, and numerical fields such as start,
    # end, or score are not checked for constraints.

    importer = get_bed_importer(Path(data_path.LOC, "test_data_fail.bed").as_posix())
    importer.parse_records()
    importer.close()
    records = importer.get_buffer()
    expected_records = [
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "",
            "start": -1,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "A",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "",
        },
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m5C",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m5C",
            "score": 1000,
            "strand": "+",
        },
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
        },
    ]
    assert expected_records == records
    dtypes = {c.name: c.type.python_type for c in Data.__table__.columns}
    for record in records:
        assert type(record["chrom"]) == dtypes["chrom"]
        assert type(record["start"]) == dtypes["start"]
        assert type(record["end"]) == dtypes["end"]
        assert type(record["name"]) == dtypes["name"]
        assert type(record["score"]) == dtypes["score"]
        assert type(record["strand"]) == dtypes["strand"]

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Dataset)
        num_records = session.execute(stmt).scalar()
        assert num_records == 0
        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        assert num_records == 0


def test_buffer(Session):
    # test with Data model, but could be any model
    # there is no check on type, data, etc.
    expected_records = [
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
            "thick_start": 0,
            "thick_end": 10,
            "item_rgb": "0,0,0",
            "coverage": 10,
            "frequency": 1,
            "dataset_id": "123456789ABC",
            "modification_id": 1,
        },
        {
            "chrom": "1",
            "start": 10,
            "end": 20,
            "name": "m6A",
            "score": 500,
            "strand": "-",
            "thick_start": 10,
            "thick_end": 20,
            "item_rgb": "10,10,10",
            "coverage": 20,
            "frequency": 2,
            "dataset_id": "123456789ABC",
            "modification_id": 2,
        },
    ]
    buffer = get_buffer(Data)
    for r in expected_records:
        buffer.buffer_data(r)
    buffer.flush()
    Session().commit()
    assert buffer._buffer == []

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        assert num_records == 2
        records = session.execute(select(Data)).scalars().all()
        for idx, record in enumerate(records):
            assert record.id == idx + 1
            assert record.eufid == expected_records[idx]["dataset_id"]
            assert record.modification_id == expected_records[idx]["modification_id"]
            assert record.chrom == expected_records[idx]["chrom"]
            assert record.start == expected_records[idx]["start"]
            assert record.end == expected_records[idx]["end"]
            assert record.name == expected_records[idx]["name"]
            assert record.score == expected_records[idx]["score"]
            assert record.strand == expected_records[idx]["strand"]
            assert record.thick_start == expected_records[idx]["thick_start"]
            assert record.thick_end == expected_records[idx]["thick_end"]
            assert record.item_rgb == expected_records[idx]["item_rgb"]
            assert record.coverage == expected_records[idx]["coverage"]
            assert record.frequency == expected_records[idx]["frequency"]


def test_buffer_no_flush(Session):
    # test with Data model, but could be any model
    # there is no check on type, data, etc.
    expected_records = [
        {
            "chrom": "1",
            "start": 0,
            "end": 10,
            "name": "m6A",
            "score": 1000,
            "strand": "+",
            "thick_start": 0,
            "thick_end": 10,
            "item_rgb": "0,0,0",
            "coverage": 10,
            "frequency": 1,
            "dataset_id": "123456789ABC",
            "modification_id": 1,
        },
        {
            "chrom": "1",
            "start": 10,
            "end": 20,
            "name": "m6A",
            "score": 500,
            "strand": "-",
            "thick_start": 10,
            "thick_end": 20,
            "item_rgb": "10,10,10",
            "coverage": 20,
            "frequency": 2,
            "dataset_id": "123456789ABC",
            "modification_id": 2,
        },
    ]
    buffer = get_buffer(Data, no_flush=True)
    for r in expected_records:
        buffer.buffer_data(r)
    Session().commit()
    assert buffer._buffer == expected_records

    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        assert num_records == 0
