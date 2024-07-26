from pathlib import Path
from posixpath import join as urljoin

import pytest

import scimodom.utils.specifications as specs
from tests.mocks.web_service import MockWebService
from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
    Taxa,
    Taxonomy,
)
from scimodom.services.annotation import (
    EnsemblAnnotationService,
    AnnotationNotFoundError,
)
from scimodom.services.file import AssemblyFileType


class MockDataService:
    def __init__(self):
        pass

    def get_modification_by_dataset(self, datasets):
        pass


class MockBedToolsService:
    def __init__(self):  # noqa
        pass

    def ensembl_to_bed_features(self, annotation_path, chrom_file, features):
        pass

    def annotate_data_using_ensembl(self, annotation_path, features, records):
        pass

    def get_ensembl_annotation_records(
        self, annotation_path, annotation_id, intergenic_feature
    ):
        pass


class MockExternalService:
    def __init__(self):
        pass


class MockFileService:
    @staticmethod
    def get_assembly_file_path(
        taxa_id: int,
        file_type: AssemblyFileType,
        chain_file_name: str | None = None,
        chain_assembly_name: str | None = None,
    ) -> Path:
        if file_type == AssemblyFileType.CHAIN:
            return Path(
                f"/data/assembly/{taxa_id}/{chain_assembly_name}/{chain_file_name}"
            )
        else:
            return Path(f"/data/assembly/{taxa_id}/{file_type.value}")

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
        file_service=MockFileService(),
    )


# tests


def test_init(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    assert service._version == "EyRBnPeVwbzW"


def test_get_annotation(Session):
    with Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert annotation.release == 110
    assert annotation.taxa_id == 9606
    assert annotation.source == "ensembl"
    assert annotation.version == "EyRBnPeVwbzW"


def test_get_annotation_fail(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    with pytest.raises(AnnotationNotFoundError) as exc:
        service.get_annotation(9606)
    assert (str(exc.value)) == "No such ensembl annotation for taxonomy ID: 9606."
    assert exc.type == AnnotationNotFoundError


def test_get_release_path(Session):
    with Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    expected_release_path = Path("/data", "annotation", "Homo_sapiens", "GRCh38", "110")
    assert release_path == expected_release_path


def test_release_exists(Session):
    with Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        genomic_annotation = GenomicAnnotation(
            id="ENSG00000000001", annotation_id=1, name="A", biotype="protein_coding"
        )
        session.add_all([version, taxonomy, taxa, annotation, genomic_annotation])
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert service._release_exists(annotation.id)


def test_ensembl_annotation_paths(Session):
    with Session() as session, session.begin():
        version = AnnotationVersion(version_num="EyRBnPeVwbzW")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        annotation = Annotation(
            release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"
        )
        session.add_all([version, taxonomy, taxa, annotation])
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
        specs.ENSEMBL_FTP,
        "release-110",
        "gtf",
        "homo_sapiens",
        expected_annotation_file,
    )
    assert annotation_file == expected_annotation_path
    assert url == expected_url
