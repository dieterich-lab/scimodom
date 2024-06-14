from io import StringIO

import pytest
from sqlalchemy import func, select

from scimodom.database.models import Data
from scimodom.services.importer.base import (
    BaseImporter,
    MissingDataError,
)
from scimodom.services.importer.data import EUFDataImporter


def _get_record(fmt=None):
    # Data specs
    record = {
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
        "dataset_id": "123456789abc",
        "modification_id": 1,
    }
    if fmt == "minimum":
        record["start"] = -1
    elif fmt == "chrom":
        record["chrom"] = "A"
    elif fmt == "strand":
        record["strand"] = ""
    elif fmt == "maximum":
        record["frequency"] = 200
    elif fmt == "modification":
        record["name"] = "m5C"
        record["modification_id"] = 2
    else:
        pass
    return record


def _get_data(EUF_specs):
    # format and version are taken from specs
    # but string is hard coded!
    format, version, specs = EUF_specs
    string = f"""#fileformat={format}v{version}

    1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1
    1\t-1\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1
    A\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1
    1\t0\t10\tm6A\t1000\t\t0\t10\t0,0,0\t10\t1
    1\t0\t10\tm5C\t1000\t+\t0\t10\t0,0,0\t10\t1
    1\t0\t10\tm5C\t1000\t+
    1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t200"""
    return StringIO(string)


def _get_data_with_header(fmt):
    # names must match those of the model, and not that of the EUF/bedRMod specs!
    skiprows = 0
    comment = "#"
    if fmt == "first":
        string = """chrom\tstart\tend\tname\tscore\tstrand\tthick_start\tthick_end\titem_rgb\tcoverage\tfrequency
        1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1"""
    elif fmt == "second":
        string = """# ignore this line
        chrom\tstart\tend\tname\tscore\tstrand\tthick_start\tthick_end\titem_rgb\tcoverage\tfrequency
        1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1"""
    if fmt == "third":
        string = """skip this line
        # ignore this line
        chrom\tstart\tend\tname\tscore\tstrand\tthick_start\tthick_end\titem_rgb\tcoverage\tfrequency
        1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1"""
        skiprows = 1
    elif fmt == "comment":
        string = """@ ignore this line
        chrom\tstart\tend\tname\tscore\tstrand\tthick_start\tthick_end\titem_rgb\tcoverage\tfrequency
        1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1"""
        comment = "@"
    elif fmt == "wrong":
        string = """chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
        1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1"""
    return skiprows, comment, StringIO(string)


@pytest.mark.parametrize(
    "fmt,msg",
    [
        ("minimum", "Value start: -1 out of range."),
        (
            "chrom",
            "Unrecognized chrom: A. Ignore this warning for scaffolds and contigs, otherwise this could be due to misformatting!",
        ),
        ("strand", "Unrecognized strand: ."),
        ("maximum", "Value frequency: 200 out of range."),
        ("modification", "Unrecognized name: m5C."),
    ],
)
def test_importer_parse_record_fail(fmt, msg, Session, EUF_specs):
    format, version, specs = EUF_specs
    expected_record = _get_record(fmt)
    importer = EUFDataImporter(
        session=Session(),
        filen="filen",
        handle=StringIO("filen"),
        eufid="123456789abc",
        association={"m6A": 1},
        seqids=["1"],
        specs_ver=version,
    )
    with pytest.raises(ValueError) as exc:
        importer.parse_record(expected_record)
    assert str(exc.value) == msg
    assert exc.type == ValueError


def test_importer_parse_record(Session, EUF_specs):
    format, version, specs = EUF_specs
    expected_record = _get_record(fmt=None)
    importer = EUFDataImporter(
        session=Session(),
        filen="filen",
        eufid="123456789abc",
        handle=StringIO("filen"),
        association={"m6A": 1},
        seqids=["1"],
        specs_ver=version,
    )
    record = importer.parse_record(expected_record)
    assert record["chrom"] == expected_record["chrom"]
    assert record["start"] == expected_record["start"]
    assert record["end"] == expected_record["end"]
    assert record["name"] == expected_record["name"]
    assert record["score"] == expected_record["score"]
    assert record["strand"] == expected_record["strand"]
    assert record["thick_start"] == expected_record["thick_start"]
    assert record["thick_end"] == expected_record["thick_end"]
    assert record["item_rgb"] == expected_record["item_rgb"]
    assert record["coverage"] == expected_record["coverage"]
    assert record["frequency"] == expected_record["frequency"]
    assert record["dataset_id"] == "123456789abc"
    assert record["modification_id"] == 1
    # types
    dtypes = {c.name: c.type.python_type for c in Data.__table__.columns}
    assert type(record["chrom"]) == dtypes["chrom"]
    assert type(record["start"]) == dtypes["start"]
    assert type(record["end"]) == dtypes["end"]
    assert type(record["name"]) == dtypes["name"]
    assert type(record["score"]) == dtypes["score"]
    assert type(record["strand"]) == dtypes["strand"]
    assert type(record["thick_start"]) == dtypes["thick_start"]
    assert type(record["thick_end"]) == dtypes["thick_end"]
    assert type(record["item_rgb"]) == dtypes["item_rgb"]
    assert type(record["coverage"]) == dtypes["coverage"]
    assert type(record["frequency"]) == dtypes["frequency"]
    assert type(record["dataset_id"]) == dtypes["dataset_id"]
    assert type(record["modification_id"]) == dtypes["modification_id"]


def test_importer_parse_records(Session, EUF_specs):
    format, version, specs = EUF_specs
    handle = _get_data(EUF_specs)
    importer = EUFDataImporter(
        session=Session(),
        filen="filen",
        eufid="123456789abc",
        handle=handle,
        association={"m6A": 1},
        seqids=["1"],
        specs_ver=version,
    )
    # warnings are emitted, this is expected, use caplog to assert them...
    importer.parse_records()
    importer.close()
    with Session() as session, session.begin():
        stmt = select(func.count()).select_from(Data)
        num_records = session.execute(stmt).scalar()
        records = session.execute(select(Data)).scalars().all()[0]
        assert num_records == 1
        assert records.id == 1
        assert records.eufid == "123456789abc"
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


@pytest.mark.parametrize(
    "fmt",
    [("first"), ("second"), ("third"), ("comment")],
)
def test_base_importer_header(fmt, Session):
    skiprows, comment, handle = _get_data_with_header(fmt)

    class TestBaseImporter(BaseImporter):
        def __init__(self):
            super().__init__(
                session=Session(),
                filen="filen",
                handle=handle,
                model=Data,
                sep="\t",
                header=None,
                skiprows=skiprows,
                comment=comment,
            )

        def parse_record(record):
            return record

    importer = TestBaseImporter()
    importer._validate_columns()
    expected_header = [
        "chrom",
        "start",
        "end",
        "name",
        "score",
        "strand",
        "thick_start",
        "thick_end",
        "item_rgb",
        "coverage",
        "frequency",
    ]
    assert importer._header == expected_header


def test_base_importer_columns_fail(Session):
    skiprows, comment, handle = _get_data_with_header("wrong")

    class TestBaseImporter(BaseImporter):
        def __init__(self):
            super().__init__(
                session=Session(),
                filen="filen",
                handle=handle,
                model=Data,
                sep="\t",
                header=None,
                skiprows=skiprows,
                comment=comment,
            )

        def parse_record(record):
            return record

    importer = TestBaseImporter()
    with pytest.raises(Exception) as exc:
        importer._validate_columns()
    assert (
        str(exc.value)
        == "Column name chromStart doesn't match any of the ORM mapped attribute names for Data. This can be caused by a file header with wrong column names, or a change in model declaration. Aborting transaction!"
    )


def test_base_importer_comment_fail(Session):
    class TestBaseImporter(BaseImporter):
        def __init__(self):
            super().__init__(
                session=Session(),
                filen="filen",
                handle=StringIO("filen"),
                model=Data,
                sep="\t",
                header=None,
                comment="##",
            )

        def parse_record(record):
            return record

    with pytest.raises(ValueError) as exc:
        importer = TestBaseImporter()
    assert str(exc.value) == "Maximum length of 1 expected, got 2 for comment."
    assert exc.type == ValueError


def test_importer_missing_data(Session, EUF_specs):
    # pass the raise_missing argument to close

    format, version, specs = EUF_specs
    handle = _get_data(EUF_specs)
    importer = EUFDataImporter(
        session=Session(),
        filen="filen",
        eufid="123456789abc",
        handle=handle,
        association={"m6A": 1},
        seqids=["1"],
        specs_ver=version,
    )
    # warnings are emitted, this is expected, use caplog to assert them...
    importer.parse_records()
    with pytest.raises(MissingDataError) as exc:
        importer.close(raise_missing=True)
    assert exc.type == MissingDataError
