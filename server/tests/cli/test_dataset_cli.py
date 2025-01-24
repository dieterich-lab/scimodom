from datetime import datetime
from pathlib import Path
import re

import pytest
from flask import Flask
from sqlalchemy import func, select

from scimodom.database.models import (
    DataAnnotation,
    Data,
    DatasetModificationAssociation,
    Dataset,
    GenomicAnnotation,
    Project,
)
from scimodom.cli.dataset import dataset_cli
from scimodom.cli.charts import charts_cli
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.dataset import DatasetService
from scimodom.services.external import ExternalService
from scimodom.services.gene import GeneService
from scimodom.services.file import FileService
from scimodom.services.project import ProjectService
from scimodom.services.selection import SelectionService
from scimodom.services.sunburst import SunburstService
from scimodom.services.validator import ValidatorService
from scimodom.services.web import WebService
from scimodom.utils.specs.enums import AnnotationSource, SunburstChartType
from tests.mocks.enums import MockEnsembl


DATA_DIR = Path(Path(__file__).parent, "data")


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

EXPECTED_SEARCH_CHART = """[{"name": "Search", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 4}]}]}]}]}]"""
EXPECTED_BROWSE_CHART = """[{"name": "Browse", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}]}]"""
EXPECTED_CHARTS = {
    "search": EXPECTED_SEARCH_CHART,
    "browse": EXPECTED_BROWSE_CHART,
}

EXPECTED_SEARCH_CHART = """[{"name": "Search", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 4}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""
EXPECTED_BROWSE_CHART = """[{"name": "Browse", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""
EXPECTED_CHARTS_BATCH = {
    "search": EXPECTED_SEARCH_CHART,
    "browse": EXPECTED_BROWSE_CHART,
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
def dataset_runner():
    app = Flask(__name__)
    app.register_blueprint(dataset_cli)
    yield app.test_cli_runner()


@pytest.fixture
def charts_runner():
    app = Flask(__name__)
    app.register_blueprint(charts_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path, charts_runner):
    mocker.patch(
        "scimodom.services.sunburst.get_file_service",
        return_value=_get_file_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_sunburst_service",
        return_value=_get_sunburst_service(Session, tmp_path, charts_runner),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_dataset_service",
        return_value=_get_dataset_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_assembly_service",
        return_value=_get_assembly_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_project_service",
        return_value=_get_project_service(Session, tmp_path),
    )
    mocker.patch(
        "scimodom.cli.dataset.get_file_service",
        return_value=_get_file_service(Session, tmp_path),
    )
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)


# tests


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
def test_add_dataset(
    Session,
    dataset_runner,
    datafiles,
    selection,
    project,
    test_data,
    tmp_path,
    freezer,
    capsys,
    mock_services,
):
    args = [
        "dataset",
        "add",
        "--assembly-id",
        1,
        "--annotation",
        "ensembl",
        "-m",
        1,
        "-m",
        2,
        "-o",
        1,
        "-t",
        1,
        Path(datafiles, "file1.bedrmod").as_posix(),
        project[0].id,
        "Dataset title CLI test",
    ]

    freezer.move_to("2024-06-20 12:00:00")
    result = dataset_runner.invoke(args=args, input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0
    # result.stdout or output does not capture secho consistently...
    eufid = re.search("EUFID: '(.*)'.", capsys.readouterr().out).group(1)

    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "Dataset title CLI test"
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
                dataset_id=eufid
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
    dataset_runner,
    datafiles,
    selection,
    project,
    test_data,
    tmp_path,
    freezer,
    capsys,
    mock_services,
):
    args = [
        "dataset",
        "add",
        "--assembly-id",
        1,
        "--annotation",
        "ensembl",
        "-m",
        1,
        "-m",
        2,
        "-o",
        1,
        "-t",
        1,
        "--dry-run",
        Path(datafiles, "file1.bedrmod").as_posix(),
        project[0].id,
        "Dataset title CLI test",
    ]

    freezer.move_to("2024-06-20 12:00:00")
    result = dataset_runner.invoke(args=args, input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
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


@pytest.mark.datafiles(Path(DATA_DIR, "file1.bedrmod"))
@pytest.mark.datafiles(Path(DATA_DIR, "file2.bedrmod"))
def test_add_dataset_in_batch(
    Session,
    dataset_runner,
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
        "--annotation",
        "ensembl",
        datafiles.as_posix(),
        "test_request",
    ]

    result = dataset_runner.invoke(args=args)
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 1
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
            assert fh.read() == EXPECTED_CHARTS_BATCH[chart_type.value]
