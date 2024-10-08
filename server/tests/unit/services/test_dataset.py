from datetime import datetime
from io import StringIO
from typing import Any

import pytest
from sqlalchemy import select, func
from sqlalchemy.sql.operators import and_

from scimodom.database.models import (
    BamFile,
    Dataset,
    DatasetModificationAssociation,
    Assembly,
    Data,
)
from scimodom.services.annotation import AnnotationSource
from scimodom.services.dataset import (
    DatasetService,
    SpecsError,
    DatasetHeaderError,
    DatasetUpdateError,
)
from scimodom.utils.bed_importer import BedImportEmptyFile, BedImportTooManyErrors
from scimodom.utils.common_dto import Strand


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


class MockBedToolsService:
    def create_temp_euf_file(self, records):  # noqa
        return "xxx"


class MockAssemblyService:
    def __init__(self, is_latest: bool, assemblies_by_id: dict[int, Assembly]):
        self._is_latest = is_latest
        self._assemblies_by_id = assemblies_by_id

    def get_assembly_by_id(self, assembly_id: int) -> Assembly:
        return self._assemblies_by_id[assembly_id]

    def is_latest_assembly(self, assembly: Assembly) -> bool:  # noqa
        return self._is_latest

    def get_seqids(self, taxa_id: int) -> list[str]:  # noqa
        return ["1"]

    def get_name_for_version(self, taxa_id: int) -> str:  # noqa
        return "GHRc38"

    def liftover(
        self,
        assembly: Assembly,
        raw_file: str,
        unmapped_file: str | None = None,
        threshold: float = 0.3,
    ) -> str:
        pass


class MockAnnotationService:
    def __init__(self, check_source_result):
        self._check_source_result = check_source_result

    def check_annotation_source(
        self, annotation_source: AnnotationSource, modification_ids: list[int]
    ):  # noqa
        return self._check_source_result

    def annotate_data(
        self,
        taxa_id: int,
        annotation_source: AnnotationSource,
        eufid: str,
        selection_ids: list[int],
    ):
        pass


def _get_dataset_service(
    session, is_latest_asembly=True, assemblies_by_id=None, check_source_result=True
):
    if assemblies_by_id is None:
        assemblies_by_id = {
            1: Assembly(
                name="GRCh38", alt_name="hg38", taxa_id=9606, version="GcatSmFcytpU"
            ),
            2: Assembly(
                name="GRCm38", alt_name="mm10", taxa_id=10090, version="GcatSmFcytpU"
            ),
            3: Assembly(
                name="GRCh37", alt_name="hg19", taxa_id=9606, version="J9dit7Tfc6Sb"
            ),
        }
    return DatasetService(
        session=session,
        file_service=MockFileService(session),
        bedtools_service=MockBedToolsService(),  # noqa
        assembly_service=MockAssemblyService(
            is_latest=is_latest_asembly, assemblies_by_id=assemblies_by_id
        ),  # noqa
        annotation_service=MockAnnotationService(
            check_source_result=check_source_result
        ),  # noqa
    )


GOOD_EUF_FILE = """#fileformat=bedRModv1.7
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


@pytest.mark.parametrize(
    "regexp,replacement",
    [
        (r"XXX", "XXX"),  # Unchange
        (r"\Z", "\n   \n "),  # Extra white space in the end
        (r"#organism=9606", "# organism = 9606 "),
        (r"\Z", "# Extra comment\n# In the end"),
    ],
)
def test_import_simple(
    regexp, replacement, Session, selection, project, freezer
):  # noqa
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    service = _get_dataset_service(Session())
    file = StringIO(euf_file)
    freezer.move_to("2017-05-20 11:00:23")
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project.id,
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
        assert dataset.project_id == project.id
        assert dataset.technology_id == 1
        assert dataset.organism_id == 1
        assert dataset.date_added == datetime(2017, 5, 20, 11, 0, 23)
        assert dataset.modification_type == "RNA"
        assert dataset.sequencing_platform == "Sequencing platform"
        assert dataset.basecalling is None
        assert dataset.bioinformatics_workflow == "Workflow"
        assert dataset.experiment == "Description of experiment."
        assert dataset.external_source is None

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


def test_import_dry_run(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    file = StringIO(GOOD_EUF_FILE)
    freezer.move_to("2017-05-20 11:00:23")
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project.id,
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


def test_import_update_no_change(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    freezer.move_to("2017-05-20 11:00:23")
    project_id = project.id
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


def test_import_update_with_change(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    freezer.move_to("2017-05-20 11:00:23")
    project_id = project.id
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


def test_import_update_fail(Session, selection, project, freezer):  # noqa
    service = _get_dataset_service(Session())
    with pytest.raises(DatasetUpdateError) as exc:
        service.import_dataset(
            StringIO(GOOD_EUF_FILE),
            source="test",
            smid=project.id,
            title="title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
            eufid="XXXXXXXXXXXX",
        )
    assert str(exc.value) == "No such dataset: 'XXXXXXXXXXXX'."
    assert exc.type == DatasetUpdateError


@pytest.mark.parametrize(
    "regexp,replacement,exception,message,record_tuples",
    [
        (
            r"#fileformat=bedRModv1.7",
            "",
            SpecsError,
            "Failed to parse version from header (1).",
            [],
        ),
        (
            r"#fileformat=bedRModv1.7",
            r"#fileformat=bedRModvXX",
            SpecsError,
            "Failed to parse version from header (2).",
            [],
        ),
        (
            r"#fileformat=bedRModv1.7",
            "#fileformat=bedRModv2.1",
            SpecsError,
            "Unknown or outdated version 2.1.",
            [],
        ),
        (
            r"#assembly=GRCh38",
            "",
            SpecsError,
            "Required header 'assembly' is missing.",
            [],
        ),
        (
            r"#assembly=GRCh38",
            "#assembly=",
            SpecsError,
            "Required header 'assembly' is empty.",
            [],
        ),
        (
            r"#organism=9606",
            "#organism=10090",
            DatasetHeaderError,
            "Expected 9606 for organism; got 10090 from file header.",
            [],
        ),
        (
            r"#assembly=GRCh38",
            "#assembly=GRCm38",
            DatasetHeaderError,
            "Expected GRCh38 for assembly; got GRCm38 from file header.",
            [],
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.bed_importer",
                    30,
                    "test, line 13: Expected 11 fields, but got 10",
                ),
                (
                    "scimodom.utils.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "",
            BedImportEmptyFile,
            "Did not find any records in 'test'",
            [("scimodom.utils.bed_importer", 40, "Did not find any records in 'test'")],
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.bed_importer",
                    30,
                    "test, line 13: Unrecognized name: m6.",
                ),
                (
                    "scimodom.utils.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "2\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.bed_importer",
                    30,
                    "test, line 13: Unrecognized chrom: 2. Ignore this warning for scaffolds and contigs, otherwise this could be due to misformatting!",
                ),
                (
                    "scimodom.utils.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
    ],
)
def test_bad_import(
    regexp,
    replacement,
    exception,
    message,
    record_tuples,
    Session,
    selection,
    project,
    freezer,
    caplog,
):  # noqa
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    service = _get_dataset_service(Session())
    file = StringIO(euf_file)
    freezer.move_to("2017-05-20 11:00:23")
    with pytest.raises(exception) as exc:
        service.import_dataset(
            file,
            source="test",
            smid=project.id,
            title="title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
        )
    assert str(exc.value) == message
    assert caplog.record_tuples == record_tuples


def test_delete_dataset(Session, dataset, bam_file):
    service = _get_dataset_service(Session())
    service.delete_dataset(dataset[0])

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Dataset)) == 1
        eufid0 = dataset[0].id
        eufid1 = dataset[1].id
        remaining_dataset = session.get_one(Dataset, eufid1)  # noqa
        for eufid, expected_length in zip([eufid0, eufid1], [0, 1]):
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
        assert service._file_service.deleted_bam_files == ["d1_1.bam", "d1_2.bam"]
