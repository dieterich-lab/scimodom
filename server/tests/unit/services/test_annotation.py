from pathlib import Path

import pytest

from scimodom.database.models import GenomicAnnotation
from scimodom.services.annotation import AnnotationService, AnnotationVersionError


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
    # taxid is wrong but does not matter as id has priority
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


# due to scope of data_path this must be called before the rest...
def test_download_annotation(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AnnotationService(Session(), annotation_id=1)
    ret_code = service._download_annotation()
    # only assert if created
    assert ret_code == 0
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
    ret_code = service._download_annotation()
    assert ret_code == 1
