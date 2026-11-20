from pathlib import Path
from posixpath import join as urljoin

import pytest
from sqlalchemy import select, update

from scimodom.database.models import (
    AnnotationRelease,
    Annotation,
    AnnotationVersion,
    GenomicAnnotation,
)
from scimodom.services.annotation import (
    EnsemblAnnotationService,
    AnnotationNotFoundError,
)
from scimodom.services.ensembl import EnsemblAssemblyClient
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


def _mock_organism_and_assembly(taxa_id):
    if taxa_id == 9606:
        return "Homo sapiens", "Homo_sapiens", "GRCh38"
    return "Mus musculus", "Mus_musculus", "GRCm38"


class MockFileService:
    @staticmethod
    def get_annotation_dir(taxa_id, assembly_name=None):
        _, name, current_assembly = _mock_organism_and_assembly(taxa_id)
        if assembly_name is None:
            assembly_name = current_assembly
        return Path("/data", "annotation", name, assembly_name)

    @classmethod
    def get_annotation_release_dir(cls, taxa_id, source, release, assembly_name=None):
        return Path(
            cls.get_annotation_dir(taxa_id, assembly_name=assembly_name),
            source,
            str(release),
        )


class MockAssemblyService:
    @staticmethod
    def get_organism(taxa_id):
        return _mock_organism_and_assembly(taxa_id)[0]

    @staticmethod
    def get_name_for_version(taxa_id):
        return _mock_organism_and_assembly(taxa_id)[2]


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
        ensembl_client=EnsemblAssemblyClient(MockWebService(url_to_result)),  # noqa
    )


# tests


def test_init(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    assert service._version == "EyRBnPeVwbzW"


def test_get_annotation(Session, setup, mocker):
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert annotation.release == 110
    assert annotation.inst_assembly.name == "GRCh38"
    assert annotation.inst_assembly.taxa_id == 9606
    assert annotation.source == "ensembl"
    assert annotation.version == "EyRBnPeVwbzW"


def test_get_annotation_any_release(Session, setup, mocker):
    # the annotation row states which release an annotation is; it is
    # no longer checked against a global one, which is what forced
    # every organism into lockstep. A second release on the same
    # assembly is what an annotation-only upgrade produces.
    with Session() as session, session.begin():
        session.execute(
            update(Annotation)
            .where(Annotation.version == "EyRBnPeVwbzW", Annotation.assembly_id == 1)
            .values(release=111)
        )
        session.add(AnnotationRelease(source="ensembl", release=111, archive="jan2024"))
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert annotation.release == 111
    assert annotation.inst_assembly.name == "GRCh38"


def test_get_annotation_fail(Session):
    with Session() as session, session.begin():
        session.add(AnnotationVersion(version_num="EyRBnPeVwbzW"))
    service = _get_ensembl_annotation_service(Session)
    with pytest.raises(AnnotationNotFoundError) as exc:
        service.get_annotation(9606)
    assert (str(exc.value)) == "No such ensembl annotation for taxonomy ID: 9606."
    assert exc.type == AnnotationNotFoundError


def test_get_release_path(Session, setup, mocker):
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    release_path = service.get_release_path(annotation)
    # the source is part of the path, cf. uq_annotation_rtv
    expected_release_path = Path(
        "/data", "annotation", "Homo_sapiens", "GRCh38", "ensembl", "110"
    )
    assert release_path == expected_release_path


def test_release_exists(Session, setup, mocker):
    with Session() as session, session.begin():
        genomic_annotation = GenomicAnnotation(
            id="ENSG00000000001", annotation_id=1, name="A", biotype="protein_coding"
        )
        session.add(genomic_annotation)
    service = _get_ensembl_annotation_service(Session)
    annotation = service.get_annotation(9606)
    assert service._release_exists(annotation.id)


def test_ensembl_annotation_paths(Session, setup, mocker):
    mocker.patch("scimodom.services.ensembl.Ensembl", MockEnsembl)
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
        "ensembl",
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


def test_release_path_follows_the_annotation_not_the_current_assembly(
    Session, setup, mocker
):
    # the whole point of the FK: an annotation on an assembly that is
    # no longer current still resolves to its own directory
    with Session() as session, session.begin():
        # GRCh37 (id 3) is not the current assembly
        session.execute(
            update(Annotation).where(Annotation.release == 109).values(assembly_id=3)
        )
    service = _get_ensembl_annotation_service(Session)
    current = service.get_annotation_from_taxid_and_source(9606, "ensembl")
    assert current.release == 110
    assert service.get_release_path(current) == Path(
        "/data", "annotation", "Homo_sapiens", "GRCh38", "ensembl", "110"
    )
    old_annotation = service._session.execute(
        select(Annotation).where(Annotation.release == 109)
    ).scalar_one()
    assert service.get_release_path(old_annotation) == Path(
        "/data", "annotation", "Homo_sapiens", "GRCh37", "ensembl", "109"
    )


def test_annotation_version_is_read_on_each_access(Session, setup):
    # an upgrade changes the current version; a service built once at
    # start-up must not keep handing out the version it saw then
    service = _get_ensembl_annotation_service(Session)
    assert service.get_annotation(9606).release == 110
    service._session.execute(
        update(AnnotationVersion).values(version_num="A8syx5TzWlK0")
    )
    service._session.commit()
    # same service instance, no rebuild
    assert service.get_annotation(9606).release == 109
