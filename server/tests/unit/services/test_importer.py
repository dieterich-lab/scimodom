import pytest


def _get_header(EUF_version, fmt=None):
    from io import StringIO
    from scimodom.utils.specifications import SPECS_EUF

    specs = SPECS_EUF.copy()
    specs_format = specs.pop("format")
    _ = specs.pop("header")
    _ = specs.pop("delimiter")
    version = EUF_version
    expected_version = f"{specs_format}v{version}"
    if fmt == "string":
        string = f"completelyWrongHeaderButVersionIs Ok{version}"
    elif fmt == "version":
        string = "#fileformat=bedRModv0.0"
    elif fmt == "EOF":
        string = ""
    elif fmt == "full":  # add blank spaces for some lines... this should work
        string = f"""#fileformat=bedRModv{EUF_version}
        #organism= 9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=   Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source="""
    elif fmt == "misformatted":
        string = f"""#fileformat=bedRModv{EUF_version}
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
        string = f"""#fileformat=bedRModv{EUF_version}
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
    elif fmt == "columns_extra":  # some misformatted columns... (case-insensitive)
        if EUF_version == "1.6":
            string = """#fileformat=bedRModv1.6
            #chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\trgb\tcoverage\tfrequency\trefBase\textra"""
        elif EUF_version == "1.7":
            string = """#fileformat=bedRModv1.7
            #chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\trgb\tcoverage\tfrequency\textra"""
    elif fmt == "columns_short":
        string = f"""#fileformat=bedRModv{EUF_version}
        #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage"""
    elif fmt == "data":
        if EUF_version == "1.6":
            string = """#fileformat=bedRModv1.6
            1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10\tA"""
        elif EUF_version == "1.7":
            string = """#fileformat=bedRModv1.7
            1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10"""
    elif fmt == "data_short":
        string = f"""#fileformat=bedRModv{EUF_version}
        1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50"""
    elif fmt == "data_type":
        if EUF_version == "1.6":
            string = """#fileformat=bedRModv1.6
            1\t139219\tstring\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10\tA"""
        elif EUF_version == "1.7":
            string = """#fileformat=bedRModv1.7
            1\t139219\tstring\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10"""
    elif fmt == "data_type_float":
        if EUF_version == "1.6":
            string = """#fileformat=bedRModv1.6
            1\t139219\tstring\tm6A\t100\t+\t139219\t139220\t0,0,0\t50.0\t10.1\tA"""
        elif EUF_version == "1.7":
            string = """#fileformat=bedRModv1.7
            1\t139219\tstring\tm6A\t100\t+\t139219\t139220\t0,0,0\t50.0\t10.1"""
    else:
        string = expected_version
    return expected_version, StringIO(string)


def _get_file(EUF_version):
    from io import StringIO

    if EUF_version == "1.6":
        string = """#fileformat=bedRModv1.6
        #organism=9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source=
        #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency\trefBase
        1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10\tA
        1\t139220\t139221\tm6A\t5\t+\t139220\t139221\t0,0,0\t100\t5\tA
        1\t139221\t139222\tm6A\t5\t+\t139221\t139222\t0,0,0\t300\t5\tA
        1\t139222\t139223\tm6A\t500\t+\t139222\t139223\t0,0,0\t250\t100\tA
        1\t139223\t139224\tm6A\t5\t+\t139223\t139224\t0,0,0\t10\t5\tA"""
    elif EUF_version == "1.7":
        string = """#fileformat=bedRModv1.7
        #organism=9606
        #modification_type=RNA
        #assembly=GRCh38
        #annotation_source=Annotation
        #annotation_version=Version
        #sequencing_platform=Sequencing platform
        #basecalling=
        #bioinformatics_workflow=Workflow
        #experiment=Description of experiment.
        #external_source=
        #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
        1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10
        1\t139220\t139221\tm6A\t5\t+\t139220\t139221\t0,0,0\t100\t5
        1\t139221\t139222\tm6A\t5\t+\t139221\t139222\t0,0,0\t300\t5
        1\t139222\t139223\tm6A\t500\t+\t139222\t139223\t0,0,0\t250\t100
        1\t139223\t139224\tm6A\t5\t+\t139223\t139224\t0,0,0\t10\t5"""
    return StringIO(string)


@pytest.mark.parametrize(
    "fmt",
    [
        (None),
        ("string"),
        ("version"),
        ("EOF"),
    ],
)
def test_importer_read_version(fmt, Session, EUF_version):
    from scimodom.services.importer import EUFImporter, SpecsError

    version, handle = _get_header(EUF_version, fmt)
    importer = EUFImporter(
        Session(),
        "fileformat",
        handle,
        "ABCDEFGH",
        "123456789ABC",
        "Title",
        9606,
        1,
        False,
    )
    if fmt == "version":
        with pytest.raises(SpecsError) as excinfo:
            importer._read_version()
    elif fmt == "EOF":
        with pytest.raises(EOFError) as excinfo:
            importer._read_version()
    else:
        importer._read_version()
        assert version == importer._version


@pytest.mark.parametrize(
    "fmt",
    [
        ("full"),
        ("misformatted"),
        ("missing"),
    ],
)
def test_importer_read_header(fmt, Session, EUF_version):
    from sqlalchemy import select
    from scimodom.services.importer import EUFImporter, SpecsError
    from scimodom.database.models import Dataset

    _, handle = _get_header(EUF_version, fmt)
    importer = EUFImporter(
        Session(),
        "fileformat",
        handle,
        "ABCDEFGH",
        "123456789ABC",
        "Title",
        9606,
        1,
        False,
    )
    importer._lino = 1
    importer._read_version()
    importer._validate_attributes(Dataset, importer._specs["headers"].values())
    importer._buffers["Dataset"] = EUFImporter._Buffer(session=Session(), model=Dataset)
    if fmt == "full":
        importer._read_header()
        assert importer._lino == len(importer._specs["headers"])
        with Session() as session, session.begin():
            records = session.execute(select(Dataset)).scalar()
            assert records.id == "123456789ABC"
            assert records.project_id == "ABCDEFGH"
            assert records.title == "Title"
            assert records.file_format == f"bedRModv{EUF_version}"
            assert records.modification_type == "RNA"
            assert records.taxa_id == 9606
            assert records.assembly_id == 1
            assert records.lifted is False
            assert records.annotation_source == "Annotation"
            assert records.annotation_version == "Version"
            assert records.sequencing_platform == "Sequencing platform"
            assert records.basecalling is None
            assert records.bioinformatics_workflow == "Workflow"
            assert records.experiment == "Description of experiment."
            assert records.external_source is None
    else:
        with pytest.raises(SpecsError) as excinfo:
            importer._read_header()


@pytest.mark.parametrize(
    "fmt",
    [
        ("columns_extra"),
        ("columns_short"),
    ],
)
def test_importer_validate_columns(fmt, Session, EUF_version):
    from scimodom.services.importer import EUFImporter, SpecsError

    _, handle = _get_header(EUF_version, fmt)
    importer = EUFImporter(
        Session(),
        "fileformat",
        handle,
        "ABCDEFGH",
        "123456789ABC",
        "Title",
        9606,
        1,
        False,
    )
    importer._lino = 1
    importer._read_version()
    if fmt == "columns_extra":
        importer._validate_columns(next(importer._handle))
    else:
        with pytest.raises(SpecsError) as excinfo:
            importer._validate_columns(next(importer._handle))


@pytest.mark.parametrize(
    "fmt",
    [
        ("data"),
        ("data_short"),
        ("data_type"),
        ("data_type_float"),
    ],
)
def test_importer_read_line(fmt, Session, caplog, EUF_version):
    from sqlalchemy import select
    from scimodom.services.importer import EUFImporter, SpecsError
    from scimodom.database.models import Data

    _, handle = _get_header(EUF_version, fmt)
    importer = EUFImporter(
        Session(),
        "fileformat",
        handle,
        "ABCDEFGH",
        "123456789ABC",
        "Title",
        9606,
        1,
        False,
    )
    importer._lino = 1
    importer._read_version()
    importer._validate_attributes(Data, importer._specs["columns"].values())
    importer._buffers["Data"] = EUFImporter._Buffer(session=Session(), model=Data)
    importer._int_types = [
        i
        for i, v in enumerate(importer._specs["columns"].values())
        if v
        in [
            "start",
            "end",
            "score",
            "thick_start",
            "thick_end",
            "coverage",
            "frequency",
        ]
    ]

    line = next(importer._handle)
    if fmt == "data":
        importer._read_line(line)
        importer._buffers["Data"].flush()
        with Session() as session, session.begin():
            records = session.execute(select(Data)).scalar()
            assert records.chrom == "1"
            assert records.start == 139219
            assert records.end == 139220
            assert records.name == "m6A"
            assert records.score == 100
            assert records.thick_start == 139219
            assert records.thick_end == 139220
            assert records.item_rgb == "0,0,0"
            assert records.coverage == 50
            assert records.frequency == 10
            # assert records.ref_base == "A"
    else:
        # currently ValueError is excepted into a warning, wrong line is skipped...
        # but does this includes TypeError?
        importer._read_line(line)
        assert "Warning: Failed to parse fileformat at row 1:" in caplog.text


def test_importer(Session, setup, project_template, EUF_version):
    from scimodom.services.importer import EUFImporter
    from scimodom.services.project import ProjectService
    from scimodom.services.dataset import Data, DataService
    from scimodom.database.models import Dataset
    import scimodom.database.queries as queries
    import scimodom.utils.utils as utils
    from sqlalchemy import select

    import uuid
    import shortuuid
    import pandas as pd

    # the order is that defined in the model...
    columns = utils.get_table_columns(Data)

    metadata = project_template["metadata"][0]
    taxa_id = metadata["organism"]["taxa_id"]
    with Session() as session, session.begin():
        session.add_all(setup)
        session.flush()
        query = queries.query_column_where(
            "Assembly", "id", filters={"name": metadata["organism"]["assembly"]}
        )
        assembly_id = session.execute(query).scalar()
        session.commit()

    ProjectService(Session(), project_template).create_project()

    u = uuid.uuid4()
    smid = shortuuid.encode(u)[: ProjectService.SMID_LENGTH]
    u = uuid.uuid4()
    eufid = shortuuid.encode(u)[: DataService.EUFID_LENGTH]
    filen = "tabStringIO"
    title = "Title"

    importer = EUFImporter(
        Session(),
        filen,
        _get_file(EUF_version),
        smid,
        eufid,
        title,
        taxa_id,
        assembly_id,
        False,
    )
    importer.parseEUF()
    importer.close()

    with Session() as session, session.begin():
        records = session.execute(select(Dataset)).scalar()
        assert records.id == eufid
        assert records.project_id == smid
        assert records.title == title
        assert records.file_format == f"bedRModv{EUF_version}"
        assert records.modification_type == "RNA"
        assert records.taxa_id == 9606
        assert records.assembly_id == assembly_id
        assert records.lifted is False
        assert records.annotation_source == "Annotation"
        assert records.annotation_version == "Version"
        assert records.sequencing_platform == "Sequencing platform"
        assert records.basecalling is None
        assert records.bioinformatics_workflow == "Workflow"
        assert records.experiment == "Description of experiment."
        assert records.external_source is None
        records = session.execute(select(Data)).scalars().all()
        df = pd.DataFrame(
            [
                (
                    r.chrom,
                    r.start,
                    r.end,
                    r.name,
                    r.score,
                    r.strand,
                    r.thick_start,
                    r.thick_end,
                    r.item_rgb,
                    r.coverage,
                    r.frequency,
                    # r.ref_base,
                )
                for r in records
            ],
            columns=columns[2:],
        )
        expected_df = pd.read_csv(
            _get_file(EUF_version),
            sep="\t",
            skiprows=12,
            header=None,
            names=columns[2:],
        )
        expected_df = expected_df.astype(importer._dtypes["Data"])
        pd.testing.assert_frame_equal(df, expected_df, check_exact=True)
