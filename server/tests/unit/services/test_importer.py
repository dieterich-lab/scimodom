import pytest


# def _get_header(variant=False):
# from io import StringIO
# from scimodom.services.importer import specsEUF

# specs = specsEUF.copy()
# fmt = specs.pop("format")
# _ = specs.pop("header")
# _ = specs.pop("delimiter")
# version = next(iter(specs))
# expected_version = f"{fmt}v{version}"
# if variant:
# fmt = fmt.lower()
# csvString = f"#fileformat={fmt}v{version}"
# csvStringIO = StringIO(csvString)
# return expected_version, csvStringIO


def _get_file():
    from io import StringIO

    tabString = """#fileformat=bedRModv1.6
    #organism=9606
    #modification_type=RNA
    #assembly=GRCh38
    #annotation_source=Ensembl
    #annotation_version=
    #sequencing_platform=Illumina NovaSeq 6000
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
    return StringIO(tabString)


# @pytest.mark.parametrize(
# "project,variant",
# [
# ("_get_header", False),
# ("_get_header", True),
# ],
# )
# def test_importer_read_version(project, variant, Session, setup, project_template):
# from scimodom.services.importer import EUFImporter
# import scimodom.database.queries as queries

# metadata = project_template["metadata"][0]

# with Session() as session, session.begin():
# session.add_all(setup)
# query = queries.query_column_where(
# "Assembly", "id", filters={"name": metadata["organism"]["assembly"]}
# )
# assembly_id = session.execute(query).scalar()

# version, handle = _get_header(variant)
# importer = EUFImporter(
# Session(),
# "csvStringIO",
# handle,
# "ABCDEFGH",
# "123456789ABC",
# "Title",
# metadata["organism"]["taxa_id"],
# assembly_id,
# False,
# )
# importer._read_version()
# assert version == importer._version


def test_importer(Session, setup, project_template):
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
        _get_file(),
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
        assert records.file_format == "bedRModv1.6"
        assert records.modification_type == "RNA"
        assert records.taxa_id == 9606
        assert records.assembly_id == assembly_id
        assert records.lifted is False
        assert records.annotation_source == "Ensembl"
        assert records.annotation_version == ""  # is None
        assert records.sequencing_platform == "Illumina NovaSeq 6000"
        assert records.basecalling == ""  # is None
        assert records.bioinformatics_workflow == "Workflow"
        assert records.experiment == "Description of experiment."
        assert records.external_source == ""  # is None
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
                    r.ref_base,
                )
                for r in records
            ],
            columns=columns[2:],
        )
        expected_df = pd.read_csv(
            _get_file(), sep="\t", skiprows=12, header=None, names=columns[2:]
        )
        expected_df = expected_df.astype(importer._dtypes["Data"])
        pd.testing.assert_frame_equal(df, expected_df, check_exact=True)
