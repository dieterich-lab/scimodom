from pathlib import Path

import pytest

from scimodom.database.models import GenomicAnnotation
from scimodom.services.annotation import AnnotationService, AnnotationVersionError


# for now simple
# gtf_records = """#!genome-build GRCh38
# #!genome-version GRCh38
# 1\thavana\tgene\t1\t1000\t.\t+\t.\tgene_id "ENSG00001"; gene_version "1"; gene_name "GENE1"; gene_source "havana"; gene_biotype "non_coding";
# 1\thavana\ttranscript\t1\t1000\t.\t+\t.\tgene_id "ENSG00001"; gene_version "1"; transcript_id "ENST00001"; transcript_version "1"; gene_name "GENE1"; gene_source "havana"; gene_biotype "non_coding"; transcript_name "TRX1"; transcript_source "havana"; transcript_biotype "non_coding";
# 1\thavana\texon\t1\t1000\t.\t+\t.\tgene_id "ENSG00001"; gene_version "1"; transcript_id "ENST00001"; transcript_version "1"; exon_number "1"; gene_name "GENE1"; gene_source "havana"; gene_biotype "non_coding"; transcript_name "TRX1"; transcript_source "havana"; transcript_biotype "non_coding";
# 1\thavana\tgene\t2000\t3000\t.\t-\t.\tgene_id "ENSG00002"; gene_version "1"; gene_name "GENE2"; gene_source "havana"; gene_biotype "protein_coding";"""


# def test_init(Session, setup, data_path):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#     with pytest.raises(AssemblyVersionError) as exc:
#         service = AssemblyService.from_id(Session(), assembly_id=3)


def test_init_from_id_wrong_id(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(ValueError) as exc:
        service = AnnotationService(Session(), annotation_id=99)
    assert (str(exc.value)) == "Annotation ID = 99 not found! Aborting transaction!"
    assert exc.type == ValueError


def test_init_from_id_wrong_version(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(AnnotationVersionError) as exc:
        service = AnnotationService(Session(), annotation_id=3)
    assert (
        (str(exc.value))
        == "Mismatch between current DB annotation version (EyRBnPeVwbzW) and version (A8syx5TzWlK0) from annotation ID = 3. Aborting transaction!"
    )
    assert exc.type == AnnotationVersionError


def test_init_from_id(Session, setup, data_path):
    # taxid is wrong but does not matter as id as priority
    # annotation file path is available, but file does not yet exists
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1, taxa_id=0)
    assert service._release == 110
    assert service._taxid == 9606


def test_init_from_taxid_fail(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(ValueError) as exc:
        service = AnnotationService(Session(), taxa_id=0)
    assert str(exc.value) == "Taxonomy ID = 0 not found! Aborting transaction!"
    assert exc.type == ValueError


def test_init_from_taxid(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), taxa_id=9606)
    assert service._db_version == "EyRBnPeVwbzW"
    assert service._annotation_id == 1
    assert service._release == 110


# due to scope of data_path thi smust be called before
def test_download_annotation(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1)
    service._download_annotation()
    # only assert if created
    assert service._annotation_file.is_file()


def test_download_annotation_exists_no_records(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    dest = Path(data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110")
    dest.mkdir(parents=True, exist_ok=True)
    with pytest.raises(Exception) as exc:
        service = AnnotationService(Session(), annotation_id=1)
        service._download_annotation()
    assert (
        str(exc.value)
        == f"Annotation directory {dest.as_posix()} already exists... but there is no record in GenomicAnnotation matching the current annotation 1 (9606, 110). Aborting transaction!"
    )


def test_download_annotation_exists(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
        # add random entry in GenomicAnnotation
        annotation = GenomicAnnotation(
            id="ENSG000000000000",
            annotation_id=1,
            name="GENE1",
            biotype="protein_coding",
        )
        session.add(annotation)
        session.commit()
    dest = Path(data_path.ANNOTATION_PATH, "Homo_sapiens", "GRCh38", "110")
    dest.mkdir(parents=True, exist_ok=True)
    service = AnnotationService(Session(), annotation_id=1)
    service._download_annotation()
