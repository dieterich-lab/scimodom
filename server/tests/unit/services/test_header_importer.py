from io import StringIO

import pytest
from sqlalchemy import select

from scimodom.database.models import Dataset
from scimodom.services.importer.header import EUFHeaderImporter, SpecsError


def _get_header(EUF_specs, fmt=None):
    # format and version are taken from specs
    # but string is hard coded!
    format, version, specs = EUF_specs
    if fmt == "string":
        string = f"completelyWrongHeaderButVersionIs Ok{version}"
    elif fmt == "version":
        string = "#fileformat=bedRModv0.0"
    elif fmt == "EOF":
        string = ""
    elif fmt == "full":  # add blank spaces for some lines... this should work
        string = f"""#fileformat={format}v{version}
        #organism= 9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=   Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source=
        #chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency
        chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency"""
    elif fmt == "misformatted":
        string = f"""#fileformat={format}v{version}
        #organism 9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=   Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source="""
    elif fmt == "missing":
        string = f"""#fileformat={format}v{version}
        #organism=9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=   Annotation
        #annotation_version=
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source="""
    elif fmt == "longer":
        string = f"""#fileformat={format}v{version}
        #organism=9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=   Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source=
        #methods=method
        #references=pubmed_id:12345678"""
    elif fmt == "disordered":  # fileformat must be first
        string = f"""#fileformat={format}v{version}
        #modification_type=RNA
        #sequencing_platform=Sequencing platform
        #organism= 9606
        #assembly=GRCh38
        #experiment=Description of experiment.
        #annotation_source=   Annotation
        #annotation_version=Version
        #basecalling=
        #bioinformatics_workflow=Workflow
        #external_source="""
    elif (
        fmt == "columns_extra"
    ):  # values are not checked, picks only the first record w/o #
        string = f"""#fileformat={format}v{version}
        #chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\trgb\tcoverage\tfrequency\textra
        chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\trgb\tcoverage\tfrequency\textra"""
    elif fmt == "columns_short":
        string = f"""#fileformat={format}v{version}
        #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage
        chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage"""
    elif fmt == "columns_none":
        string = f"""#fileformat={format}v{version}
        #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage
        \n"""
    else:
        string = version
    return StringIO(string)


@pytest.mark.parametrize(
    "fmt,error,msg",
    [
        (
            "version",
            SpecsError,
            "Unknown or outdated version bedRModv0.0.",
        ),  # wrong version
        ("EOF", EOFError, "filen"),  # empty
    ],
)
def test_importer_read_version_fail(fmt, error, msg, Session, EUF_specs):
    format, version, specs = EUF_specs
    handle = _get_header(EUF_specs, fmt)
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    with pytest.raises(error) as exc:
        importer._read_version()
    assert str(exc.value) == msg
    assert exc.type == error


@pytest.mark.parametrize(
    "fmt",
    [
        (None),  # expected version
        ("string"),  # wrong format but right version
    ],
)
def test_importer_read_version(fmt, Session, EUF_specs):
    format, version, specs = EUF_specs
    handle = _get_header(EUF_specs, fmt)
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    importer._read_version()
    assert importer._specs_ver == version
    assert importer._num_cols == len(specs["headers"])
    # ignore fileformat
    assert importer._required == specs["required"][1:]


@pytest.mark.parametrize(
    "fmt,msg",
    [
        ("misformatted", "#organism=."),
        ("missing", "#annotation_version=."),
    ],
)
def test_importer_parse_lines_fail(fmt, msg, Session, EUF_specs):
    handle = _get_header(EUF_specs, fmt)
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    importer._lino = 1
    importer._read_version()
    with pytest.raises(SpecsError) as exc:
        importer._parse_lines()
    assert str(exc.value) == f"Missing or misformatted header: {msg}"
    assert exc.type == SpecsError


@pytest.mark.parametrize(
    "fmt",
    [
        ("full"),
        ("longer"),
        ("disordered"),
    ],
)
def test_importer_parse_lines(fmt, Session, EUF_specs):
    handle = _get_header(EUF_specs, fmt)
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    importer._lino = 1
    importer._read_version()
    importer._parse_lines()
    assert importer._lino == importer._num_cols
    assert importer.taxid == 9606
    assert importer.assembly == "GRCh38"
    assert importer._header["id"] == "123456789ABC"
    assert importer._header["project_id"] == "ABCDEFGH"
    assert importer._header["title"] == "Title"
    assert importer._header["modification_type"] == "RNA"
    assert importer._header["sequencing_platform"] == "Sequencing platform"
    assert importer._header["basecalling"] is None
    assert importer._header["bioinformatics_workflow"] == "Workflow"
    assert importer._header["experiment"] == "Description of experiment."
    assert importer._header["external_source"] is None


@pytest.mark.parametrize(
    "fmt",
    [
        ("columns_extra"),
        ("columns_short"),
        ("columns_none"),
    ],
)
def test_importer_validate_columns(fmt, Session, EUF_specs):
    handle = _get_header(EUF_specs, fmt)
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    importer._lino = 1
    importer._read_version()
    if fmt == "columns_extra":
        importer._validate_columns()
    else:
        with pytest.raises(SpecsError) as exc:
            importer._validate_columns()
        assert (
            str(exc.value)
            == "Column count (header) doesn't match required count at row 3 for bedRModv1.7."
        )
        assert exc.type == SpecsError


def test_importer(Session, EUF_specs):
    handle = _get_header(EUF_specs, "full")
    importer = EUFHeaderImporter(
        Session(),
        filen="filen",
        handle=handle,
        smid="ABCDEFGH",
        eufid="123456789ABC",
        title="Title",
    )
    importer.parse_header()
    importer.close()
    with Session() as session, session.begin():
        records = session.execute(select(Dataset)).scalar()
        assert records.id == "123456789ABC"
        assert records.project_id == "ABCDEFGH"
        assert records.title == "Title"
        assert records.modification_type == "RNA"
        assert records.sequencing_platform == "Sequencing platform"
        assert records.basecalling is None
        assert records.bioinformatics_workflow == "Workflow"
        assert records.experiment == "Description of experiment."
        assert records.external_source is None
