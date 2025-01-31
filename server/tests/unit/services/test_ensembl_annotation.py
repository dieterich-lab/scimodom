from pathlib import Path
from posixpath import join as urljoin

import pytest

from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
)
from scimodom.services.annotation import (
    EnsemblAnnotationService,
    AnnotationNotFoundError,
    AnnotationVersionError,
)
from scimodom.utils.specs.enums import AssemblyFileType
from tests.mocks.web import MockWebService
from tests.mocks.enums import MockEnsembl


class MockDataService:
    def __init__(self):
        pass

    def get_modification_by_dataset(self, datasets):  # noqa
        pass


class MockBedToolsService:
    def __init__(self):  # noqa
        pass

    def ensembl_to_bed_features(self, annotation_path, chrom_file, features):  # noqa
        pass

    def annotate_data_using_ensembl(self, annotation_path, features, records):  # noqa
        pass

    def get_ensembl_annotation_records(
        self, annotation_path, annotation_id, intergenic_feature
    ):  # noqa
        pass


class MockExternalService:
    def __init__(self):
        pass


class MockGeneService:
    def update_gene_cache(selfselection_id: int):  # moqa
        pass


class MockFileService:
    @staticmethod
    def get_annotation_dir(taxa_id):
        if taxa_id == 9606:
            assembly = "GRCh38"
            name = "Homo_sapiens"
        else:
            assembly = "GRCm38"
            name = "Mus_musculus"
        return f"/data/annotation/{name}/{assembly}"


def _get_ensembl_annotation_service(
    Session, url_to_result: dict[str, dict] | None = None
):
    return EnsemblAnnotationService(
        session=Session(),
        data_service=MockDataService(),  # noqa
        bedtools_service=MockBedToolsService(),  # noqa
        external_service=MockExternalService(),  # noqa
        web_service=MockWebService(url_to_result),  # noqa
        gene_service=MockGeneService(),  # noqa
        file_service=MockFileService(),  # noqa
    )


# tests


def test_init(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    assert service._version == "EyRBnPeVwbzW"


def test_get_annotation(Session, setup, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert annotation.release == 110
    assert annotation.taxa_id == 9606
    assert annotation.source == "ensembl"
    assert annotation.version == "EyRBnPeVwbzW"


def test_get_annotation_wrong_specs(Session, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
        session.add(
            Annotation(
                release=111, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
            )
        )
    service = _get_ensembl_annotation_service(Session)
    with pytest.raises(AnnotationVersionError) as exc:
        service.get_annotation(9606)
    assert (
        (str(exc.value))
        == "Mismatch between annotation release '111' and current database Ensembl release '110'."
    )
    assert exc.type == AnnotationVersionError


def test_get_annotation_fail(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    with pytest.raises(AnnotationNotFoundError) as exc:
        service.get_annotation(9606)
    assert (str(exc.value)) == "No such ensembl annotation for taxonomy ID: 9606."
    assert exc.type == AnnotationNotFoundError


def test_get_release_path(Session, setup, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    expected_release_path = Path("/data", "annotation", "Homo_sapiens", "GRCh38", "110")
    assert release_path == expected_release_path


def test_release_exists(Session, setup, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    with Session() as session, session.begin():
        genomic_annotation = GenomicAnnotation(
            id="ENSG00000000001", annotation_id=1, name="A", biotype="protein_coding"
        )
        session.add(genomic_annotation)
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert service._release_exists(annotation.id)


def test_ensembl_annotation_paths(Session, setup, mocker):
    mocker.patch("scimodom.services.annotation.ensembl.Ensembl", MockEnsembl)
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    annotation_file, url = service._get_annotation_paths(annotation, release_path)
    expected_annotation_file = service.ANNOTATION_FILE(
        organism="Homo_sapiens", assembly="GRCh38", release="110", fmt="gtf"
    )
    expected_annotation_path = Path(
        "/data",
        "annotation",
        "Homo_sapiens",
        "GRCh38",
        "110",
        expected_annotation_file,
    )
    expected_url = urljoin(
        MockEnsembl.FTP.value,
        "release-110",
        "gtf",
        "homo_sapiens",
        expected_annotation_file,
    )
    assert annotation_file == expected_annotation_path
    assert url == expected_url
