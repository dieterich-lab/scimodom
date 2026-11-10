from datetime import datetime
from pathlib import Path

import pytest
from flask import Flask
from sqlalchemy import delete, func, select

from scimodom.database.models import (
    DataAnnotation,
    Data,
    DatasetModificationAssociation,
    Dataset,
    GenomicAnnotation,
    Project,
    ProjectSelection,
    Selection,
)
from scimodom.cli.dataset import dataset_cli
from scimodom.cli.chart import chart_cli
from scimodom.services.administration.ingestion import ProjectIngestionService
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.dataset import DatasetService
from scimodom.services.ensembl import EnsemblAssemblyClient
from scimodom.services.external import ExternalService
from scimodom.services.gene import GeneService
from scimodom.services.file import FileService
from scimodom.services.project import ProjectService
from scimodom.services.selection import SelectionService
from scimodom.services.sunburst import SunburstService
from scimodom.services.utilities import UtilitiesService
from scimodom.services.validator import ValidatorService
from scimodom.services.web import WebService
from scimodom.utils.specs.enums import AnnotationSource, SunburstChartType
from tests.mocks.enums import MockEnsembl

DATA_DIR = Path(Path(__file__).parent.parent, "data")


PROJECT_BATCH_REQUEST = """
{
    "title": "Request for CLI test",
    "summary": "Long summary.",
    "contact_name": "Surname, Forename",
    "contact_institution": "Institution",
    "contact_email": "test@email.de",
    "date_published": null,
    "external_sources": [],
    "metadata": [
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "Technology 1",
            "method_id": "91b145ea",
            "organism": {
                "taxa_id": 9606,
                "cto": "Cell type 1",
                "assembly_name": "GRCh38",
                "assembly_id": 1
            },
            "note": "file=file1.bedrmod, title=Dataset 1 title CLI test"
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000005C",
            "tech": "Technology 1",
            "method_id": "91b145ea",
            "organism": {
                "taxa_id": 9606,
                "cto": "Cell type 1",
                "assembly_name": "GRCh38"
            },
            "note": "file=file1.bedrmod, title=Dataset 1 title CLI test"
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "Technology 2",
            "method_id": "0ee048bc",
            "organism": {
                "taxa_id": 9606,
                "cto": "Cell type 2",
                "assembly_name": "GRCh38"
            },
            "note": "file=file2.bedrmod, title=Dataset 2 title CLI test"
        }
    ]
}
"""


EXON = """1\t65000\t65300\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t65418\t65433\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
1\t65418\t65500\tGENE3\t.\t-\tENSG00000000003\tunprocessed_pseudogene
1\t65425\t65500\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t65519\t65573\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
1\t69036\t71585\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
"""

CDS = """1\t65000\t65300\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t65425\t65450\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t65564\t65573\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
1\t69036\t70005\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
"""

UTR5 = """1\t65418\t65433\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
1\t65519\t65564\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
"""

UTR3 = """1\t65450\t65500\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t70005\t71585\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
"""

INTRON = """1\t65300\t65425\tGENE1\t.\t+\tENSG00000000001\tprotein_coding
1\t65433\t65519\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
1\t65573\t69036\tGENE2\t.\t+\tENSG00000000002\tprotein_coding
"""

INTERGENIC = """1\t0\t65000"""

FEATURES = {
    "exon.bed": EXON,
    "five_prime_utr.bed": UTR5,
    "three_prime_utr.bed": UTR3,
    "CDS.bed": CDS,
    "intron.bed": INTRON,
    "intergenic.bed": INTERGENIC,
}

EXPECTED_ANNOTATED_RECORDS = [
    (1, "ENSG00000000002", "Exonic"),
    (1, "ENSG00000000002", "5'UTR"),
    (1, "ENSG00000000001", "Intronic"),
    (2, "ENSG00000000002", "Exonic"),
    (2, "ENSG00000000002", "CDS"),
    (3, "ENSG00000000002", "Exonic"),
    (3, "ENSG00000000002", "3'UTR"),
    (4, "ENSG00000000002", "Intronic"),
    (5, "ENSIntergenic", "Intergenic"),
]


EXPECTED_RECORDS = [
    ("1", 65420, 1),
    ("1", 65565, 2),
    ("1", 71500, 3),
    ("1", 65580, 4),
    ("1", 0, 5),
]

SEARCH_CHART = """[{"name": "Search", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 4}]}]}]}]}]"""
BROWSE_CHART = """[{"name": "Browse", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}]}]"""
EXPECTED_CHARTS = {
    "search": SEARCH_CHART,
    "browse": BROWSE_CHART,
}

SEARCH_CHART = """[{"name": "Search", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 4}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""
BROWSE_CHART = """[{"name": "Browse", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""
EXPECTED_CHARTS_IN_BATCH = {
    "search": SEARCH_CHART,
    "browse": BROWSE_CHART,
}


class MockSunburstService(SunburstService):
    def __init__(self, session, file_service, cli_runner) -> None:
        self._cli_runner = cli_runner
        super().__init__(session, file_service)

    def trigger_background_update(self):
        self._cli_runner.invoke(args=["charts", "sunburst-update"])


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_assembly_service(Session, tmp_path):
    return AssemblyService(
        session=Session(),
        external_service=ExternalService(
            file_service=_get_file_service(Session, tmp_path)
        ),
        web_service=WebService(),
        file_service=_get_file_service(Session, tmp_path),
        ensembl_client=EnsemblAssemblyClient(WebService()),
    )


def _get_bedtools_service(Session, tmp_path):
    return BedToolsService(tmp_path=Path(tmp_path, "t_temp"))


def _get_gene_service(Session, tmp_path):
    return GeneService(
        session=Session(), file_service=_get_file_service(Session, tmp_path)
    )


def _get_annotation_service(Session, tmp_path):
    return AnnotationService(
        session=Session(),
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=Session(),
                data_service=DataService(Session()),
                bedtools_service=_get_bedtools_service(Session, tmp_path),
                external_service=ExternalService(
                    file_service=_get_file_service(Session, tmp_path)
                ),
                web_service=WebService(),
                gene_service=_get_gene_service(Session, tmp_path),
                file_service=_get_file_service(Session, tmp_path),
            ),
        },
    )


def _get_validator_service(Session, tmp_path):
    return ValidatorService(
        session=Session(),
        annotation_service=_get_annotation_service(Session, tmp_path),
        assembly_service=_get_assembly_service(Session, tmp_path),
        bedtools_service=_get_bedtools_service(Session, tmp_path),
    )


def _get_sunburst_service(Session, tmp_path, cli_runner):
    return MockSunburstService(
        session=Session(),
        file_service=_get_file_service(Session, tmp_path),
        cli_runner=cli_runner,
    )


def _get_selection_service(Session, tmp_path):
    return SelectionService(
        session=Session(), gene_service=_get_gene_service(Session, tmp_path)
    )


def _get_project_service(Session, tmp_path):
    return ProjectService(
        session=Session(),
        file_service=_get_file_service(Session, tmp_path),
        selection_service=_get_selection_service(Session, tmp_path),
    )


def _get_dataset_service(Session, tmp_path):
    return DatasetService(
        session=Session(),
        annotation_service=_get_annotation_service(Session, tmp_path),
        file_service=_get_file_service(Session, tmp_path),
        validator_service=_get_validator_service(Session, tmp_path),
        selection_service=_get_selection_service(Session, tmp_path),
    )


@pytest.fixture
def genomic_annotation(Session):
    annotation1 = GenomicAnnotation(
        id="ENSG00000000001", annotation_id=1, name="GENE1", biotype="protein_coding"
    )
    annotation2 = GenomicAnnotation(
        id="ENSG00000000002", annotation_id=1, name="GENE2", biotype="protein_coding"
    )
    annotation3 = GenomicAnnotation(
        id="ENSG00000000003",
        annotation_id=1,
        name="GENE3",
        biotype="unprocessed_pseudogene",
    )
    session = Session()
    session.add_all([annotation1, annotation2, annotation3])
    session.commit()


@pytest.fixture
def test_data(tmp_path, genomic_annotation):
    # add required assembly files
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "chrom.sizes", "w") as fh:
        fh.write("1\t248956422\n")
    # add required annotation files
    d = (
        tmp_path
        / "t_data"
        / FileService.ANNOTATION_DEST
        / "Homo_sapiens"
        / "GRCh38"
        / "110"
    )
    d.mkdir(parents=True, exist_ok=True)
    for feature, string in FEATURES.items():
        with open(d / feature, "w") as fh:
            fh.write(string)


@pytest.fixture
def test_request(tmp_path):
    # add required template
    d = tmp_path / "t_data" / FileService.METADATA_DEST / FileService.REQUEST_DEST
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "test_request.json", "w") as fh:
        fh.write(PROJECT_BATCH_REQUEST)


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(dataset_cli)
    app.register_blueprint(chart_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path, test_runner):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    mocker.patch(
        "scimodom.services.sunburst.get_file_service",
        return_value=_get_file_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.chart.get_sunburst_service",
        return_value=_get_sunburst_service(Session, tmp_path, test_runner),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_sunburst_service",
        return_value=_get_sunburst_service(Session, tmp_path, test_runner),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_dataset_service",
        return_value=_get_dataset_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_project_ingestion_service",
        return_value=ProjectIngestionService(
            project_service=_get_project_service(Session, tmp_path),
            assembly_service=_get_assembly_service(Session, tmp_path),
            utilities_service=UtilitiesService(session=Session()),
            file_service=_get_file_service(Session, tmp_path),
            permission_service=mocker.Mock(),
            user_service=mocker.Mock(),
            dataset_service=_get_dataset_service(Session, tmp_path),
        ),
    )


# tests


def _add_args(datafiles, smid, *extra):
    return [
        "dataset",
        "add",
        "--yes",
        *extra,
        "--assembly-id",
        1,
        "--rna-type",
        "WTS",
        "-m",
        1,
        "-m",
        2,
        "-o",
        1,
        "-t",
        1,
        smid,
        "Dataset title CLI test",
        Path(datafiles, "file1.bedrmod").as_posix(),
    ]


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
@pytest.mark.parametrize("dry_run", [False, True])
def test_add_dataset_selection_not_in_project(
    dry_run,
    Session,
    test_runner,
    datafiles,
    selection,
    project,
    test_data,
    mock_services,
    caplog,
):
    # the selections exist, but are not declared for the project
    smid = project[0].id
    extra = ["--dry-run"] if dry_run else []
    result = test_runner.invoke(args=_add_args(datafiles, smid, *extra))
    assert result.exit_code == 1
    assert (
        f"Selection with m5C, m6A, Cell type 1, and Technology 1 (9606) is not available for project '{smid}'"
        in caplog.text
    )
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 0
        assert session.scalar(select(func.count()).select_from(Data)) == 0


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_add_dataset_creates_selections(
    Session,
    test_runner,
    datafiles,
    selection,
    project_selection,
    project,
    test_data,
    mock_services,
):
    # selections are created on upload
    smid = project[0].id
    with Session() as session:
        session.execute(delete(Selection))
        session.commit()
    result = test_runner.invoke(args=_add_args(datafiles, smid))
    assert result.exit_code == 0
    with Session() as session:
        rows = session.execute(select(Selection)).scalars().all()
        assert {(r.modification_id, r.organism_id, r.technology_id) for r in rows} == {
            (1, 1, 1),
            (2, 1, 1),
        }


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_add_dataset(
    Session,
    test_runner,
    datafiles,
    selection,
    project_selection,
    project,
    test_data,
    tmp_path,
    freezer,
    mock_services,
):
    args = [
        "dataset",
        "add",
        "--yes",
        "--assembly-id",
        1,
        "--rna-type",
        "WTS",
        "-m",
        1,
        "-m",
        2,
        "-o",
        1,
        "-t",
        1,
        project[0].id,
        "Dataset title CLI test",
        Path(datafiles, "file1.bedrmod").as_posix(),
    ]

    freezer.move_to("2024-06-20 12:00:00")
    result = test_runner.invoke(args=args)
    assert result.exit_code == 0

    with Session() as session:
        dataset = session.execute(
            select(Dataset).filter_by(title="Dataset title CLI test")
        ).scalar_one()
        assert dataset.project_id == project[0].id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2024, 6, 20, 12, 0, 0)
        assert dataset.modification_type == "RNA"
        assert dataset.basecalling is None
        assert dataset.bioinformatics_workflow == "Workflow for CLI test"
        assert dataset.experiment == "Description of experiment for CLI test."
        assert dataset.external_source is None

        modifications = session.scalars(
            select(DatasetModificationAssociation.modification_id).filter_by(
                dataset_id=dataset.id
            )
        ).all()
        assert set(modifications) == set([1, 2])

        records = session.execute(select(Data)).scalars().all()
        records = set((r.chrom, r.start, r.score) for r in records)
        assert records == set(EXPECTED_RECORDS)
        annotation_records = session.scalars(select(DataAnnotation)).all()
        annotated_records = set(
            (r.data_id, r.gene_id, r.feature) for r in annotation_records
        )
        assert annotated_records == set(EXPECTED_ANNOTATED_RECORDS)

    d = tmp_path / "t_data" / FileService.GENE_CACHE_DEST
    for selection, expected_set in zip(["1", "2"], [{"GENE1", "GENE2"}, {"GENE2"}]):
        with open(Path(d, selection)) as fh:
            gene_set = set(fh.read().strip().split())
        assert gene_set == expected_set
    d = tmp_path / "t_data" / FileService.SUNBURST_CACHE_DEST
    for chart_type in SunburstChartType:
        with open(Path(d, f"{chart_type.value}.json")) as fh:
            assert fh.read() == EXPECTED_CHARTS[chart_type.value]


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_add_dataset_dry_run(
    Session,
    test_runner,
    datafiles,
    selection,
    project_selection,
    project,
    test_data,
    tmp_path,
    freezer,
    mock_services,
):
    args = [
        "dataset",
        "add",
        "--yes",
        "--assembly-id",
        1,
        "--rna-type",
        "WTS",
        "-m",
        1,
        "-m",
        2,
        "-o",
        1,
        "-t",
        1,
        "--dry-run",
        project[0].id,
        "Dataset title CLI test",
        Path(datafiles, "file1.bedrmod").as_posix(),
    ]

    freezer.move_to("2024-06-20 12:00:00")
    result = test_runner.invoke(args=args)
    assert result.exit_code == 0

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 0
        assert session.scalar(select(func.count()).select_from(Data)) == 0
        assert session.scalar(select(func.count()).select_from(DataAnnotation)) == 0
        assert (
            session.scalar(
                select(func.count()).select_from(DatasetModificationAssociation)
            )
            == 0
        )

    d = tmp_path / "t_data" / FileService.GENE_CACHE_DEST
    assert any(Path(d).iterdir()) is False
    d = tmp_path / "t_data" / FileService.SUNBURST_CACHE_DEST
    assert any(Path(d).iterdir()) is False


def _dataset_args(project_id, filename, modification_ids=(1, 2), extra=()):
    args = ["dataset", "add", "--yes", "--assembly-id", 1, "--rna-type", "WTS"]
    for mid in modification_ids:
        args.extend(["-m", mid])
    args.extend(["-o", 1, "-t", 1, *extra])
    args.extend([project_id, "Dataset title CLI test", filename])
    return args


def _record_state(Session):
    with Session() as session:
        records = session.execute(select(Data)).scalars().all()
        associations = session.execute(
            select(DatasetModificationAssociation.modification_id)
        ).scalars()
        return (
            sorted((r.chrom, r.start, r.score) for r in records),
            sorted(associations),
            session.scalar(select(func.count()).select_from(DataAnnotation)),
        )


@pytest.fixture
def existing_dataset(
    Session,
    test_runner,
    datafiles,
    selection,
    project,
    project_selection,
    test_data,
    mock_services,
):
    # create a dataset, and return the EUFID, the project, and the update file
    project_id = project[0].id
    file = Path(datafiles, "file1.bedrmod")
    result = test_runner.invoke(args=_dataset_args(project_id, file.as_posix()))
    assert result.exit_code == 0, result.output
    with Session() as session:
        eufid = session.execute(select(Dataset.id)).scalar_one()
    text = file.read_text()
    # update: new score for the first record
    updated = Path(datafiles, "updated.bedrmod")
    updated.write_text(text.replace("m6A\t1\t+", "m6A\t100\t+"))
    assert updated.read_text() != text
    return eufid, project_id, file, updated


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_update_dataset(Session, test_runner, datafiles, existing_dataset):
    eufid, project_id, _, updated = existing_dataset
    args = _dataset_args(project_id, updated.as_posix(), extra=["--eufid", eufid])
    result = test_runner.invoke(args=args)
    assert result.exit_code == 0, result.output
    records, associations, _ = _record_state(Session)
    assert records == sorted(
        [("1", 65420, 100)] + [r for r in EXPECTED_RECORDS if r[1] != 65420]
    )
    assert associations == [1, 2]
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_update_dataset_dry_run(Session, test_runner, datafiles, existing_dataset):
    eufid, project_id, _, updated = existing_dataset
    before = _record_state(Session)
    args = _dataset_args(
        project_id, updated.as_posix(), extra=["--eufid", eufid, "--dry-run"]
    )
    result = test_runner.invoke(args=args)
    assert result.exit_code == 0
    assert _record_state(Session) == before


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
@pytest.mark.datafiles(Path(DATA_DIR, "file2.bedrmod"))
def test_add_dataset_in_batch(
    Session,
    test_runner,
    datafiles,
    selection,
    test_data,
    test_request,
    tmp_path,
    mock_services,
):
    args = [
        "dataset",
        "batch",
        "--yes",
        "test_request",
        datafiles.as_posix(),
    ]

    result = test_runner.invoke(args=args)
    assert result.exit_code == 0

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 1
        # declared by the template of the new project
        assert session.scalar(select(func.count()).select_from(ProjectSelection)) == 3
        assert session.scalar(select(func.count()).select_from(Dataset)) == 2
        assert session.scalar(select(func.count()).select_from(Dataset)) == 2
        assert session.scalar(select(func.count()).select_from(Data)) == 6
        assert session.scalar(select(func.count()).select_from(DataAnnotation)) == 12
        assert (
            session.scalar(
                select(func.count()).select_from(DatasetModificationAssociation)
            )
            == 3
        )

    d = tmp_path / "t_data" / FileService.GENE_CACHE_DEST
    for selection, expected_set in zip(
        ["1", "2", "3"], [{"GENE1", "GENE2"}, {"GENE2"}, {"GENE1", "GENE2"}]
    ):
        with open(Path(d, selection)) as fh:
            gene_set = set(fh.read().strip().split())
        assert gene_set == expected_set
    d = tmp_path / "t_data" / FileService.SUNBURST_CACHE_DEST
    for chart_type in SunburstChartType:
        with open(Path(d, f"{chart_type.value}.json")) as fh:
            assert fh.read() == EXPECTED_CHARTS_IN_BATCH[chart_type.value]
