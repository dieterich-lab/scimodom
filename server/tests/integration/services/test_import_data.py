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
from scimodom.services.dataset import DatasetService
from scimodom.services.assembly import AssemblyService
from scimodom.services.annotation import AnnotationService, AnnotationSource
from scimodom.services.annotation.ensembl import EnsemblAnnotationService
from scimodom.services.annotation.gtrnadb import GtRNAdbAnnotationService
from scimodom.services.bedtools import BedToolsService
from scimodom.services.data import DataService
from scimodom.services.external import ExternalService
from scimodom.services.web import WebService
from scimodom.services.file import FileService


EXON = """1\t65418\t65433\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65418\t65500\tF\t.\t-\tENSG00000000002\tunprocessed_pseudogene
1\t65519\t65573\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t69036\t71585\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

CDS = """1\t65564\t65573\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t69036\t70005\tG \t.\t+\tENSG00000000001\tprotein_coding
"""

UTR5 = """1\t65418\t65433\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65519\t65564\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

UTR3 = """1\t70008\t71585\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

INTRON = """1\t65433\t65519\tG\t.\t+\tENSG00000000001\tprotein_coding
1\t65573\t69036\tG\t.\t+\tENSG00000000001\tprotein_coding
"""

INTERGENIC = """1\t0\t11868"""

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
#bioinformatics_workflow=Workflow
#experiment=Description of experiment.
#external_source=
#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency
1\t65420\t65421\tm6A\t1\t+\t65420\t65421\t0,0,0\t1\t1
1\t65565\t65566\tm6A\t2\t+\t65565\t65566\t0,0,0\t2\t2
1\t71500\t71501\tm6A\t3\t+\t71500\t71501\t0,0,0\t3\t3
1\t65580\t65581\tm6A\t4\t+\t65580\t65581\t0,0,0\t4\t4
1\t0\t1\tm6A\t5\t+\t0\t1\t0,0,0\t5\t5
"""


def _add_genomic_annotation(session):
    annotation = GenomicAnnotation(
        id="ENSG00000000001", annotation_id=1, name="G", biotype="protein_coding"
    )
    session.add(annotation)
    session.commit()


def _add_tmp_data(tmp_path):
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


def _get_web_service():
    return WebService()


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
    return DatasetService(
        session=session,
        file_service=file_service,
        bedtools_service=bedtools_service,
        annotation_service=annotation_service,
        assembly_service=assembly_service,
    )


# tests


def test_import_simple(Session, selection, project, tmp_path, freezer):
    service = _get_dataset_service(Session(), tmp_path)

    _add_tmp_data(tmp_path)
    _add_genomic_annotation(Session())

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

    expected_annotated_records = [
        (1, "ENSG00000000001", "Exonic"),
        (2, "ENSG00000000001", "Exonic"),
        (3, "ENSG00000000001", "Exonic"),
        (1, "ENSG00000000001", "5'UTR"),
        (2, "ENSG00000000001", "CDS"),
        (3, "ENSG00000000001", "3'UTR"),
        (4, "ENSG00000000001", "Intronic"),
        (5, "ENSIntergenic", "Intergenic"),
    ]
    expected_records = [
        ("1", 65420, 1),
        ("1", 65565, 2),
        ("1", 71500, 3),
        ("1", 65580, 4),
        ("1", 0, 5),
    ]
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
        assert dataset.bioinformatics_workflow == "Workflow"
        assert dataset.experiment == "Description of experiment."
        assert dataset.external_source is None

        records = session.execute(select(Data)).scalars().all()
        records = set((r.chrom, r.start, r.score) for r in records)
        assert records == set(expected_records)
        annotation_records = session.scalars(select(DataAnnotation)).all()
        annotated_records = set(
            (r.data_id, r.gene_id, r.feature) for r in annotation_records
        )
        assert annotated_records == set(expected_annotated_records)
        with open(tmp_path / FileService.GENE_CACHE_DEST / "1", "r") as fh:
            assert fh.read().strip() == "G"
