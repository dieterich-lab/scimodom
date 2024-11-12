from datetime import datetime
from io import StringIO

import pytest
from sqlalchemy import select

from scimodom.database.models import (
    Data,
    Dataset,
    GenomicAnnotation,
    DataAnnotation,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.annotation.gtrnadb import GtRNAdbAnnotationService
from scimodom.services.assembly import AssemblyService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.dataset import DatasetService
from scimodom.services.external import ExternalService
from scimodom.services.file import FileService
from scimodom.services.sunburst import SunburstService
from scimodom.services.web import WebService
from scimodom.services.validator import ValidatorService
from scimodom.utils.specs.enums import AnnotationSource, SunburstChartType
from tests.mocks.enums import MockEnsembl


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

EUF_FILE = """
#fileformat=bedRModv1.8
#organism=9606
#modification_type=RNA
#assembly=GRCh38
#annotation_source=Annotation
#annotation_version=Version
#sequencing_platform=Sequencing platform
#basecalling=
#bioinformatics_workflow=Workflow for integration test
#experiment=Description of experiment for integration test.
#external_source=
#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency
1\t65420\t65421\tm6A\t1\t+\t65420\t65421\t0,0,0\t1\t1
1\t65565\t65566\tm6A\t2\t+\t65565\t65566\t0,0,0\t2\t2
1\t71500\t71501\tm6A\t3\t+\t71500\t71501\t0,0,0\t3\t3
1\t65580\t65581\tm6A\t4\t+\t65580\t65581\t0,0,0\t4\t4
1\t0\t1\tm6A\t5\t+\t0\t1\t0,0,0\t5\t5
"""


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


EXPECTED_SEARCH_CHART = """[{"name": "Search", "children": [{"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 5}]}]}]}]}]"""
EXPECTED_BROWSE_CHART = """[{"name": "Browse", "children": [{"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}]}]"""
EXPECTED_CHARTS = {
    "search": EXPECTED_SEARCH_CHART,
    "browse": EXPECTED_BROWSE_CHART,
}


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
    d = tmp_path / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "chrom.sizes", "w") as fh:
        fh.write("1\t248956422\n")
    # add required annotation files
    d = tmp_path / FileService.ANNOTATION_DEST / "Homo_sapiens" / "GRCh38" / "110"
    d.mkdir(parents=True, exist_ok=True)
    for feature, string in FEATURES.items():
        with open(d / feature, "w") as fh:
            fh.write(string)


def _get_bedtools_service(tmp_path):
    return BedToolsService(tmp_path=tmp_path)


def _get_assembly_service(session, external_service, web_service, file_service):
    return AssemblyService(
        session=session,
        external_service=external_service,
        web_service=web_service,
        file_service=file_service,
    )


def _get_annotation_service(
    session,
    data_service,
    bedtools_service,
    external_service,
    web_service,
    file_service,
):
    return AnnotationService(
        session=session,
        services_by_annotation_source={
            AnnotationSource.ENSEMBL: EnsemblAnnotationService(
                session=session,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
                file_service=file_service,
            ),
            AnnotationSource.GTRNADB: GtRNAdbAnnotationService(
                session=session,
                data_service=data_service,
                bedtools_service=bedtools_service,
                external_service=external_service,
                web_service=web_service,
                file_service=file_service,
            ),
        },
    )


def _get_file_service(session, tmp_path):
    return FileService(
        session=session,
        temp_path=tmp_path,
        upload_path=tmp_path,
        data_path=tmp_path,
        import_path=tmp_path,
    )


def _get_data_service(session):
    return DataService(session=session)


def _get_external_service(file_service):
    return ExternalService(file_service=file_service)


def _get_sunburst_service(session, tmp_path):
    return SunburstService(
        session=session,
        file_service=_get_file_service(session, tmp_path),
    )


def _get_web_service():
    return WebService()


def _get_validator_service(
    session, annotation_service, assembly_service, bedtools_service
):
    return ValidatorService(
        session=session,
        annotation_service=annotation_service,
        assembly_service=assembly_service,
        bedtools_service=bedtools_service,
    )


def _get_dataset_service(session, tmp_path):
    bedtools_service = _get_bedtools_service(tmp_path)
    file_service = _get_file_service(session, tmp_path)
    data_service = _get_data_service(session)
    external_service = _get_external_service(file_service)
    web_service = _get_web_service()
    assembly_service = _get_assembly_service(
        session, external_service, web_service, file_service
    )
    annotation_service = _get_annotation_service(
        session,
        data_service,
        bedtools_service,
        external_service,
        web_service,
        file_service,
    )
    validator_service = _get_validator_service(
        session, annotation_service, assembly_service, bedtools_service
    )
    return DatasetService(
        session=session,
        annotation_service=annotation_service,
        file_service=file_service,
        validator_service=validator_service,
    )


# tests


def test_import_data(Session, selection, project, test_data, tmp_path, freezer, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    service = _get_dataset_service(Session(), tmp_path)
    file_handle = StringIO(EUF_FILE)
    freezer.move_to("2024-06-20 12:00:00")
    eufid = service.import_dataset(
        file_handle,
        source="test",
        smid=project[0].id,
        title="Dataset title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )
    # manually trigger sunburst creation
    sunburst_service = _get_sunburst_service(Session(), tmp_path)
    sunburst_service.do_background_update()

    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "Dataset title"
        assert dataset.project_id == "12345678"
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2024, 6, 20, 12, 0, 0)
        assert dataset.modification_type == "RNA"
        assert dataset.sequencing_platform == "Sequencing platform"
        assert dataset.basecalling is None
        assert dataset.bioinformatics_workflow == "Workflow for integration test"
        assert dataset.experiment == "Description of experiment for integration test."
        assert dataset.external_source is None

        records = session.execute(select(Data)).scalars().all()
        records = set((r.chrom, r.start, r.score) for r in records)
        assert records == set(EXPECTED_RECORDS)
        annotation_records = session.scalars(select(DataAnnotation)).all()
        annotated_records = set(
            (r.data_id, r.gene_id, r.feature) for r in annotation_records
        )
        assert annotated_records == set(EXPECTED_ANNOTATED_RECORDS)
        # tmp_path / FileService.GENE_CACHE_DEST / "1"
        gene_set = set(service._file_service.get_gene_cache(["1"]))
        assert gene_set == {"GENE1", "GENE2"}
        for chart_type in SunburstChartType:
            # tmp_path / FileService.SUNBURST_CACHE_DEST / chart_type.value
            with service._file_service.open_sunburst_cache(chart_type.value) as fh:
                assert fh.read() == EXPECTED_CHARTS[chart_type.value]
