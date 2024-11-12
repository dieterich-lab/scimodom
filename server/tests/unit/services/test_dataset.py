from datetime import datetime
from io import StringIO
from typing import Any, Generator

import pytest
from sqlalchemy import select, func
from sqlalchemy.sql.operators import and_

from scimodom.database.models import (
    BamFile,
    Dataset,
    DatasetModificationAssociation,
    Data,
    User,
)
from scimodom.services.dataset import DatasetService
from scimodom.services.validator import _DatasetImportContext, DatasetUpdateError
from scimodom.utils.importer.bed_importer import EufImporter
from scimodom.utils.dtos.bedtools import EufRecord
from scimodom.utils.specs.euf import EUF_HEADERS
from scimodom.utils.specs.enums import Strand, AnnotationSource


class MockFileService:
    def __init__(self, session):
        self._session = session
        self.deleted_bam_files: list[str] = []
        self.deleted_gene_cache: list[int] = []

    def delete_gene_cache(self, selection_id: int) -> None:
        self.deleted_gene_cache.append(selection_id)

    def remove_bam_file(self, bam_file):
        self.deleted_bam_files.append(bam_file.original_file_name)
        self._session.delete(bam_file)
        self._session.commit()

    def get_bam_file(self, dataset: Dataset, name: str) -> BamFile:
        return self._session.scalars(
            select(BamFile).where(
                and_(
                    BamFile.dataset_id == dataset.id, BamFile.original_file_name == name
                )
            )
        ).one()

    def get_bam_file_list(self, dataset: Dataset) -> list[dict[str, Any]]:
        items = self._session.scalars(
            select(BamFile).where(BamFile.dataset_id == dataset.id)
        ).all()
        return [self._get_bam_file_info(i) for i in items]

    @staticmethod
    def _get_bam_file_info(bam_file):
        return {
            "original_file_name": bam_file.original_file_name,
        }


class MockAnnotationService:
    def __init__(self):
        self._annotated = False

    def annotate_data(
        self,
        taxa_id: int,
        annotation_source: AnnotationSource,
        eufid: str,
        selection_ids: list[int],
    ):
        self._annotated = True


class MockValidatorService:
    def __init__(self):
        self._context: _DatasetImportContext
        self._read_header: dict[str, str]

    @staticmethod
    def get_validated_records(
        importer: EufImporter, context: _DatasetImportContext
    ) -> Generator[EufRecord, None, None]:  # noqa
        for record in importer.parse():
            yield record

    def create_import_context(self, importer: EufImporter, **kwargs) -> None:
        kwargs = {**kwargs, "taxa_id": 9606}
        self._context = _DatasetImportContext(**kwargs)
        self._context.selection_ids = [1]
        self._context.modification_names = {"m6A": 1}

        read_header = {}
        for header_tag, internal_name in EUF_HEADERS.items():
            value = importer.get_header(header_tag)
            read_header[internal_name] = value
        self._read_header = read_header

    def get_import_context(self) -> _DatasetImportContext:
        return self._context

    def get_validated_header(self) -> dict[str, str]:
        return self._read_header


def _get_dataset_service(session):
    return DatasetService(
        session=session,
        annotation_service=MockAnnotationService(),
        file_service=MockFileService(session),
        validator_service=MockValidatorService(),
    )


GOOD_EUF_FILE = """#fileformat=bedRModv1.8
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
1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1
"""


# tests

# NOTE: the importer is not mocked!


def test_dataset_get_by_id(Session, dataset):  # noqa
    service = _get_dataset_service(Session())
    d1 = service.get_by_id("dataset_id01")
    assert d1.title == "dataset title"
    assert d1.organism_id == 1
    assert d1.external_source == "ext. source 1"
    assert d1.date_added == datetime(2024, 10, 21, 8, 10, 27)


def test_get_datasets(Session, project, dataset):  # noqa
    service = _get_dataset_service(Session())
    datasets = service.get_datasets()
    assert len(datasets) == 4
    assert datasets[3]["project_id"] == "ABCDEFGH"
    assert datasets[3]["dataset_id"] == "dataset_id04"
    assert datasets[3]["modomics_sname"] == "m5C"
    assert datasets[3]["taxa_sname"] == "H. sapiens"
    assert datasets[3]["cto"] == "Cell type 2"


def test_get_datasets_for_user(Session, project, dataset):  # noqa
    with Session() as session:
        user = session.get_one(User, 1)
    service = _get_dataset_service(Session())
    datasets = service.get_datasets(user)
    assert len(datasets) == 3


@pytest.mark.parametrize(
    "regexp,replacement",
    [
        (r"XXX", "XXX"),  # Unchange
        (r"\Z", "\n   \n "),  # Extra white space in the end
        (r"#organism=9606", "# organism = 9606 "),
        (r"\Z", "# Extra comment\n# In the end"),
    ],
)
def test_import_dataset(
    regexp, replacement, Session, selection, project, freezer
):  # noqa
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    service = _get_dataset_service(Session())
    file = StringIO(euf_file)
    project_id = project[0].id
    freezer.move_to("2017-05-20 11:00:23")
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "title"
        assert dataset.project_id == project_id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)
        assert dataset.modification_type == "RNA"
        assert dataset.sequencing_platform == "Sequencing platform"
        assert dataset.basecalling is None
        assert dataset.bioinformatics_workflow == "Workflow"
        assert dataset.experiment == "Description of experiment."
        assert dataset.external_source is None

        association = (
            session.execute(select(DatasetModificationAssociation)).scalars().all()
        )
        assert len(association) == 1
        assert association[0].dataset_id == eufid
        assert association[0].modification_id == 1

        data = (
            session.execute(select(Data).where(Data.dataset_id == eufid))
            .scalars()
            .all()
        )
        assert len(data) == 1
        assert data[0].chrom == "1"
        assert data[0].start == 0
        assert data[0].name == "m6A"
        assert data[0].strand == Strand.FORWARD
        assert data[0].score == 1000

    assert service._annotation_service._annotated is True


def test_import_dataset_dry_run(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    file = StringIO(GOOD_EUF_FILE)
    freezer.move_to("2017-05-20 11:00:23")
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project[0].id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dry_run_flag=True,
        eufid="XXXXXXXXXXXX",
    )

    assert eufid == "DRYRUNDRYRUN"
    with Session() as session:
        datasets = session.execute(select(Dataset)).all()
        assert len(datasets) == 0
        data = session.execute(select(Data)).all()
        assert len(data) == 0
        association = session.execute(select(DatasetModificationAssociation)).all()
        assert len(association) == 0

    assert service._annotation_service._annotated is False


def test_import_dataset_update_no_change(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    freezer.move_to("2017-05-20 11:00:23")
    project_id = project[0].id
    eufid = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        smid=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1

    new_eufid = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        smid=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        eufid=eufid,
    )

    assert new_eufid == eufid
    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "title"
        assert dataset.project_id == project_id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)

        data = (
            session.execute(select(Data).where(Data.dataset_id == eufid))
            .scalars()
            .all()
        )
        assert len(data) == 1
        assert data[0].chrom == "1"
        assert data[0].start == 0
        assert data[0].name == "m6A"
        assert data[0].strand == Strand.FORWARD
        assert data[0].score == 1000


def test_import_dataset_update_with_change(
    Session, selection, project, freezer
):  # noqa
    service = _get_dataset_service(Session())
    freezer.move_to("2017-05-20 11:00:23")
    project_id = project[0].id
    eufid = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        smid=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1

    new_eufid = service.import_dataset(
        StringIO(GOOD_EUF_FILE.replace("1000", "555")),
        source="test",
        smid=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        eufid=eufid,
    )

    assert new_eufid == eufid
    with Session() as session:
        dataset = session.get_one(Dataset, eufid)
        assert dataset.title == "title"
        assert dataset.project_id == project_id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)

        data = (
            session.execute(select(Data).where(Data.dataset_id == eufid))
            .scalars()
            .all()
        )
        assert len(data) == 1
        assert data[0].chrom == "1"
        assert data[0].start == 0
        assert data[0].name == "m6A"
        assert data[0].strand == Strand.FORWARD
        assert data[0].score == 555


def test_import_dataset_update_fail(Session, selection, dataset, project):  # noqa
    service = _get_dataset_service(Session())
    with pytest.raises(DatasetUpdateError) as exc:
        service.import_dataset(
            StringIO(GOOD_EUF_FILE),
            source="test",
            smid=project[0].id,
            title="dataset title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
            eufid="XXXXXXXXXXXX",
        )
    assert str(exc.value) == "No such dataset: 'XXXXXXXXXXXX'."
    assert exc.type == DatasetUpdateError


def test_delete_dataset(Session, dataset, bam_file):
    service = _get_dataset_service(Session())
    # delete d1, d3, d4, keep d2
    service.delete_dataset(dataset[0])
    service.delete_dataset(dataset[2])
    service.delete_dataset(dataset[3])

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1
        eufid0 = dataset[0].id
        eufid1 = dataset[1].id
        eufid2 = dataset[2].id
        eufid3 = dataset[3].id
        for eufid, expected_length in zip(
            [eufid0, eufid1, eufid2, eufid3], [0, 1, 0, 0]
        ):
            data = (
                session.execute(select(Data).where(Data.dataset_id == eufid))
                .scalars()
                .all()
            )
            assert len(data) == expected_length
            dataset_association = (
                session.execute(
                    select(DatasetModificationAssociation).filter_by(dataset_id=eufid)
                )
                .scalars()
                .all()
            )
            assert len(dataset_association) == expected_length
            bam_list = (
                session.execute(select(BamFile).filter_by(dataset_id=eufid))
                .scalars()
                .all()
            )
            assert len(bam_list) == expected_length
        assert service._file_service.deleted_bam_files == [
            "dataset_id01_1.bam",
            "dataset_id01_2.bam",
        ]
