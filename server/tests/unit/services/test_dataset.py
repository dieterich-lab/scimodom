from datetime import datetime
from io import StringIO
from typing import Any, Generator

from pathlib import Path

import pytest
from sqlalchemy import delete, select, func
from sqlalchemy.sql.operators import and_

from scimodom.database.models import (
    BamFile,
    Dataset,
    DatasetModificationAssociation,
    Data,
    Selection,
    User,
)
from scimodom.services.dataset import DatasetService
from scimodom.services.selection import SelectionService
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
        self.removed_files: list[Path] = []
        self.bam_records_at_remove: int | None = None

    def delete_gene_cache(self, selection_id: int) -> None:
        self.deleted_gene_cache.append(selection_id)

    def delete_bam_file_records(self, dataset: Dataset) -> list[Path]:
        paths = []
        for bam_file in self._session.scalars(
            select(BamFile).where(BamFile.dataset_id == dataset.id)
        ).all():
            self.deleted_bam_files.append(bam_file.original_file_name)
            paths.append(Path("/data/bam", bam_file.storage_file_name))
            self._session.delete(bam_file)
        return paths

    def remove_files(self, paths) -> None:
        # state of the bam_file table when the files are removed
        self.bam_records_at_remove = self._session.scalar(
            select(func.count()).select_from(BamFile)
        )
        self.removed_files = list(paths)

    def get_bam_file(self, dataset: Dataset, name: str) -> BamFile:
        return self._session.scalars(
            select(BamFile).where(
                and_(
                    BamFile.dataset_id == dataset.id, BamFile.original_file_name == name
                )
            )
        ).one()

    def get_bam_info_list(self, dataset: Dataset) -> list[dict[str, Any]]:
        items = self._session.scalars(
            select(BamFile).where(BamFile.dataset_id == dataset.id)
        ).all()
        return [self._get_bam_file_info(i) for i in items]

    @staticmethod
    def _get_bam_file_info(bam_file):
        return {
            "original_file_name": bam_file.original_file_name,
        }


class MockGeneService:
    pass


class MockAnnotationService:
    def __init__(self):
        self._annotated = False
        self._selection_ids = None

    def annotate_data(
        self,
        taxa_id: int,
        annotation_source: AnnotationSource,
        dataset_id: str,
        selection_ids: list[int],
    ):
        self._annotated = True
        self._selection_ids = selection_ids


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
        self._context.modification_names = {"m6A": {"short_name": "m6A", "id": 1}}

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
        selection_service=SelectionService(session, gene_service=MockGeneService()),
    )


GOOD_EUF_FILE = """#fileformat=bedRModvXX
#organism=9606
#modification_type=RNA
#modification_names=m6A:m6A:A
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
    d1 = service.get_by_id("dataset00001")
    assert d1.title == "dataset title"
    assert d1.organism_id == 1
    assert d1.external_source == "ext. source 1"
    assert d1.date_added == datetime(2024, 10, 21, 8, 10, 27)


def test_get_dataset_count(Session, dataset):
    service = _get_dataset_service(Session())
    assert service.get_dataset_count() == 4


def test_get_dataset_count_for_user(Session, project, dataset):
    with Session() as session:
        user = session.get_one(User, 1)
    service = _get_dataset_service(Session())
    assert service.get_dataset_count(user) == 3


def test_get_datasets(Session, project, dataset):  # noqa
    service = _get_dataset_service(Session())
    datasets = service.get_datasets()
    assert len(datasets) == 4
    assert datasets[3]["project_id"] == "ABCDEFGH"
    assert datasets[3]["dataset_id"] == "dataset00004"
    assert datasets[3]["rna_type"] == "WTS"
    assert datasets[3]["modifications"] == "m5C"
    assert datasets[3]["modification_type"] == "RNA"
    assert datasets[3]["taxa_short_name"] == "H. sapiens"
    assert datasets[3]["cto"] == "Cell type 2"
    assert "project_title" not in datasets[3]
    assert "project_summary" not in datasets[3]
    assert "doi" not in datasets[3]
    assert "pmid" not in datasets[3]


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
    dataset_id = service.import_dataset(
        file,
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        dataset = session.get_one(Dataset, dataset_id)
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
        assert association[0].dataset_id == dataset_id
        assert association[0].modification_id == 1

        data = (
            session.execute(select(Data).where(Data.dataset_id == dataset_id))
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


def _import(service, project_id, **kwargs):
    return service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        **kwargs,
    )


def test_import_dataset_uses_existing_selection(Session, selection, project):  # noqa
    project_id = project[0].id
    service = _get_dataset_service(Session())
    with Session() as session:
        expected = session.execute(
            select(Selection.id).filter_by(
                modification_id=1, organism_id=1, technology_id=1
            )
        ).scalar_one()
    _import(service, project_id)
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Selection)) == 5
    assert service._annotation_service._selection_ids == [expected]


def test_import_dataset_creates_selection(Session, selection, project):  # noqa
    project_id = project[0].id
    # the selection does not exist (e.g. deleted with the last dataset)
    with Session() as session:
        session.execute(delete(Selection))
        session.commit()
    service = _get_dataset_service(Session())
    _import(service, project_id)
    with Session() as session:
        selections = session.execute(select(Selection)).scalars().all()
        assert len(selections) == 1
        assert (
            selections[0].modification_id,
            selections[0].organism_id,
            selections[0].technology_id,
        ) == (1, 1, 1)
        assert service._annotation_service._selection_ids == [selections[0].id]


def test_import_dataset_dry_run_does_not_create_selection(
    Session, selection, project  # noqa
):
    project_id = project[0].id
    with Session() as session:
        session.execute(delete(Selection))
        session.commit()
    service = _get_dataset_service(Session())
    _import(service, project_id, dry_run_flag=True)
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Selection)) == 0
    assert service._annotation_service._annotated is False


def test_import_dataset_dry_run(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    file = StringIO(GOOD_EUF_FILE)
    freezer.move_to("2017-05-20 11:00:23")
    dataset_id = service.import_dataset(
        file,
        source="test",
        project_id=project[0].id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dry_run_flag=True,
    )

    assert dataset_id == "DRYRUNDRYRUN"
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
    dataset_id = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1

    new_dataset_id = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dataset_id=dataset_id,
    )

    assert new_dataset_id == dataset_id
    with Session() as session:
        dataset = session.get_one(Dataset, dataset_id)
        assert dataset.title == "title"
        assert dataset.project_id == project_id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)

        data = (
            session.execute(select(Data).where(Data.dataset_id == dataset_id))
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
    dataset_id = service.import_dataset(
        StringIO(GOOD_EUF_FILE),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
    )

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1

    new_dataset_id = service.import_dataset(
        StringIO(GOOD_EUF_FILE.replace("1000", "555")),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dataset_id=dataset_id,
    )

    assert new_dataset_id == dataset_id
    with Session() as session:
        dataset = session.get_one(Dataset, dataset_id)
        assert dataset.title == "title"
        assert dataset.project_id == project_id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)

        data = (
            session.execute(select(Data).where(Data.dataset_id == dataset_id))
            .scalars()
            .all()
        )
        assert len(data) == 1
        assert data[0].chrom == "1"
        assert data[0].start == 0
        assert data[0].name == "m6A"
        assert data[0].strand == Strand.FORWARD
        assert data[0].score == 555


def _import_new_dataset(service, project_id, **kwargs):
    args = {
        "source": "test",
        "project_id": project_id,
        "title": "title",
        "assembly_id": 1,
        "modification_ids": [1],
        "technology_id": 1,
        "organism_id": 1,
        "annotation_source": AnnotationSource.ENSEMBL,
    }
    args.update(kwargs)
    return service.import_dataset(
        StringIO(kwargs.pop("euf_file", GOOD_EUF_FILE)), **args
    )


def _get_state(Session):
    with Session() as session:
        data = session.execute(
            select(Data.id, Data.dataset_id, Data.name, Data.score)
        ).all()
        association = session.execute(
            select(
                DatasetModificationAssociation.dataset_id,
                DatasetModificationAssociation.modification_id,
            )
        ).all()
        datasets = session.execute(select(Dataset.id, Dataset.title)).all()
    return data, association, datasets


def test_import_dataset_dry_run_unknown_eufid(Session, selection, project):  # noqa
    service = _get_dataset_service(Session())
    with pytest.raises(DatasetUpdateError) as exc:
        service.import_dataset(
            StringIO(GOOD_EUF_FILE),
            source="test",
            project_id=project[0].id,
            title="title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
            dry_run_flag=True,
            dataset_id="XXXXXXXXXXXX",
        )
    assert str(exc.value) == "No such dataset: 'XXXXXXXXXXXX'."
    assert _get_state(Session) == ([], [], [])


def test_import_dataset_update_dry_run(Session, selection, project):  # noqa
    service = _get_dataset_service(Session())
    project_id = project[0].id
    dataset_id = _import_new_dataset(service, project_id)
    before = _get_state(Session)
    assert [row.score for row in before[0]] == [1000]
    service._annotation_service._annotated = False

    # valid update (new scores), not applied
    result = service.import_dataset(
        StringIO(GOOD_EUF_FILE.replace("1000", "555")),
        source="test",
        project_id=project_id,
        title="title",
        assembly_id=1,
        modification_ids=[1],
        technology_id=1,
        organism_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dry_run_flag=True,
        dataset_id=dataset_id,
    )
    assert result == dataset_id
    assert _get_state(Session) == before
    assert service._annotation_service._annotated is False


def test_import_dataset_update_fail(Session, selection, dataset, project):  # noqa
    service = _get_dataset_service(Session())
    with pytest.raises(DatasetUpdateError) as exc:
        service.import_dataset(
            StringIO(GOOD_EUF_FILE),
            source="test",
            project_id=project[0].id,
            title="dataset title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
            dataset_id="XXXXXXXXXXXX",
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
        for dataset_id, expected_length in zip(
            [eufid0, eufid1, eufid2, eufid3], [0, 1, 0, 0]
        ):
            data = (
                session.execute(select(Data).where(Data.dataset_id == dataset_id))
                .scalars()
                .all()
            )
            assert len(data) == expected_length
            dataset_association = (
                session.execute(
                    select(DatasetModificationAssociation).filter_by(
                        dataset_id=dataset_id
                    )
                )
                .scalars()
                .all()
            )
            assert len(dataset_association) == expected_length
            bam_list = (
                session.execute(select(BamFile).filter_by(dataset_id=dataset_id))
                .scalars()
                .all()
            )
            assert len(bam_list) == expected_length
        assert service._file_service.deleted_bam_files == [
            "dataset00001_1.bam",
            "dataset00001_2.bam",
        ]


def test_delete_dataset_removes_bam_files_after_commit(Session, dataset, bam_file):
    service = _get_dataset_service(Session())
    names = [
        b.storage_file_name
        for b in Session().scalars(select(BamFile).filter_by(dataset_id="dataset00001"))
    ]
    service.delete_dataset(dataset[0])
    assert [p.name for p in service._file_service.removed_files] == names
    # records of dataset[0] are gone from the database, but not the one of dataset[1]
    assert service._file_service.bam_records_at_remove == 1


def _counts(session):
    return {
        model: session.scalar(select(func.count()).select_from(model))
        for model in (Dataset, Data, DatasetModificationAssociation, BamFile)
    }


@pytest.mark.parametrize("failing_step", ["delete_bam_file_records", "commit"])
def test_delete_dataset_is_atomic(Session, dataset, bam_file, mocker, failing_step):
    service = _get_dataset_service(Session())
    session = Session()
    before = _counts(session)
    # fail late: data records and associations are already deleted (not committed)
    target = service._file_service if failing_step != "commit" else service._session
    mocker.patch.object(target, failing_step, side_effect=RuntimeError("runtime"))
    with pytest.raises(RuntimeError, match="runtime"):
        service.delete_dataset(dataset[0])
    after = _counts(session)
    # nothing was deleted: not the data, not the associations, not the BAM records
    assert after == before
    # and the files on disk are kept
    assert service._file_service.removed_files == []
