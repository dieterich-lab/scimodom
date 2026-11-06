from collections import defaultdict, namedtuple
from io import StringIO
from decimal import Decimal

import pytest
from sqlalchemy.exc import NoResultFound

from datetime import datetime

from scimodom.database.models import Assembly, Dataset, DatasetModificationAssociation
from scimodom.services.assembly import AssemblyNotFoundError
from scimodom.services.validator import (
    _DatasetImportContext,
    _ReadOnlyImportContext,
    SpecsError,
    DatasetHeaderError,
    DatasetUpdateError,
    DatasetImportError,
    SelectionNotFoundError,
    DatasetExistsError,
    ValidatorService,
)
from scimodom.utils.importer.bed_importer import (
    EufImporter,
    BedImportEmptyFile,
    BedImportTooManyErrors,
)
from scimodom.utils.specs.enums import AnnotationSource, ImportLimits, Strand
from scimodom.utils.dtos.bedtools import EufRecord

InputSelection = namedtuple(
    "InputSelection", "project_id modification organism technology assembly"
)


GOOD_EUF_FILE = """#fileformat=bedRModv2
#organism=9606
#modification_type=RNA
#modification_names=a:m6A:A
#assembly=GRCh38
#annotation_source=Annotation
#annotation_version=Version
#sequencing_platform=Sequencing platform
#basecalling=
#bioinformatics_workflow=Workflow
#experiment=Description of experiment.
#external_source=
#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency
1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1
"""


class MockBedToolsService:
    def create_temp_euf_file(self, records):  # noqa
        return "xxx"


class MockAssemblyService:
    def __init__(
        self,
        is_latest: bool,
        assemblies_by_id: dict[int, Assembly],
        assemblies_by_name: dict[int, dict[str, Assembly]],
        allowed_assemblies: dict[int, list[str]] | None,
    ):
        self._is_latest = is_latest
        self._assemblies_by_id = assemblies_by_id
        self._assemblies_by_name = assemblies_by_name
        self._allowed_assemblies = allowed_assemblies

    def get_by_id(self, assembly_id: int) -> Assembly:
        try:
            return self._assemblies_by_id[assembly_id]
        except KeyError:
            raise NoResultFound

    def get_by_taxa_and_name(self, taxa_id: int, assembly_name: str) -> Assembly:
        try:
            return self._assemblies_by_name[taxa_id][assembly_name]
        except KeyError:
            raise NoResultFound

    def add_assembly(self, taxa_id: int, assembly_name: str) -> None:
        try:
            self.get_by_taxa_and_name(taxa_id, assembly_name)
        except NoResultFound:
            if self._allowed_assemblies is None:
                raise Exception
            else:
                if assembly_name in self._allowed_assemblies[taxa_id]:
                    assembly = Assembly(
                        id=4,
                        name=assembly_name,
                        taxa_id=taxa_id,
                        version="NFrsaxAU9UjS",
                    )
                    self._assemblies_by_id.update({4: assembly})
                    self._assemblies_by_name[assembly.taxa_id].update(
                        {assembly.name: assembly}
                    )
                    return
                else:
                    raise AssemblyNotFoundError

    def is_latest_assembly(self, assembly: Assembly) -> bool:  # noqa
        return self._is_latest

    def get_chroms(self, taxa_id: int) -> list[dict[str, str | int]]:  # noqa
        return [{"chrom": "1", "size": 1000}]

    def get_name_for_version(self, taxa_id: int) -> str:  # noqa
        return "GRCh38"

    def create_lifted_file(
        self,
        assembly: Assembly,
        raw_file: str,
        unmapped_file: str | None = None,
        threshold: float = ImportLimits.LIFTOVER.max,
    ) -> StringIO:  # noqa
        regexp = "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1"
        replacement = "1\t10\t20\ta\t1000\t+\t0\t10\t0,0,0\t10\t1"
        euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
        s = StringIO(euf_file)
        s.name = "xxx"
        return s


class MockAnnotationService:
    def __init__(self, check_source_result):
        self._check_source_result = check_source_result

    def check_annotation_source(
        self, annotation_source: AnnotationSource, modification_ids: list[int]
    ):  # noqa
        return self._check_source_result


@pytest.fixture
def input_ctx(selection, project):  # noqa
    yield {
        "project_id": project[0].id,
        "dataset_id": "NEWNEWNEWNEW",
        "title": "dataset title",
        "modification_ids": [1],
        "organism_id": 1,
        "technology_id": 1,
        "assembly_id": 1,
        "annotation_source": AnnotationSource.ENSEMBL,
        "dry_run_flag": False,
        "update_flag": False,
    }


def _get_validator_service(
    session,
    is_latest_asembly=True,
    assemblies_by_id=None,
    allowed_assemblies=None,
    check_source_result=True,
):
    if assemblies_by_id is None:
        assemblies_by_id = {
            1: Assembly(
                id=1,
                name="GRCh38",
                alt_name="hg38",
                taxa_id=9606,
                version="GcatSmFcytpU",
            ),
            2: Assembly(
                id=2,
                name="GRCm38",
                alt_name="mm10",
                taxa_id=10090,
                version="GcatSmFcytpU",
            ),
            3: Assembly(
                id=3,
                name="GRCh37",
                alt_name="hg19",
                taxa_id=9606,
                version="J9dit7Tfc6Sb",
            ),
        }
    assemblies_by_name = defaultdict(dict)
    for assembly in assemblies_by_id.values():
        assemblies_by_name[assembly.taxa_id].update({assembly.name: assembly})

    return ValidatorService(
        session=session,
        bedtools_service=MockBedToolsService(),
        assembly_service=MockAssemblyService(
            is_latest=is_latest_asembly,
            assemblies_by_id=assemblies_by_id,
            assemblies_by_name=assemblies_by_name,
            allowed_assemblies=allowed_assemblies,
        ),
        annotation_service=MockAnnotationService(
            check_source_result=check_source_result
        ),
    )


# tests

# NOTE: the importer is not mocked!


def test_read_only_import_context(Session, setup):  # noqa
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session())
    service.create_read_only_import_context(importer=importer, taxa_id=9606)
    assert service.get_read_only_context() == _ReadOnlyImportContext(
        taxa_id=9606,
        assembly_id=1,
        is_liftover=False,
        chromosomes={"1": 1000},
        modification_names={"a": {"short_name": "m6A", "id": hash("m6A")}},
    )


def test_read_only_import_context_add_assembly(Session, setup):
    euf_file = GOOD_EUF_FILE.replace(r"#assembly=GRCh38", r"#assembly=NCBI36")
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(
        Session(), allowed_assemblies={9606: ["GRCh37", "GRCh38", "NCBI36"]}
    )
    service.create_read_only_import_context(importer=importer, taxa_id=9606)
    assert service.get_read_only_context() == _ReadOnlyImportContext(
        taxa_id=9606,
        assembly_id=4,
        is_liftover=False,
        chromosomes={"1": 1000},
        modification_names={"a": {"short_name": "m6A", "id": hash("m6A")}},
    )


def test_read_only_import_context_invalid_assembly(Session, setup):
    euf_file = GOOD_EUF_FILE.replace(r"#assembly=GRCh38", r"#assembly=NCBI36")
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(
        Session(), allowed_assemblies={9606: ["GRCh37", "GRCh38"]}
    )
    with pytest.raises(DatasetImportError):
        service.create_read_only_import_context(importer=importer, taxa_id=9606)


def test_create_import_context(Session, input_ctx):
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)

    assert service.get_import_context() == _DatasetImportContext(
        project_id="12345678",
        dataset_id="NEWNEWNEWNEW",
        title="dataset title",
        modification_ids=[1],
        organism_id=1,
        technology_id=1,
        annotation_source=AnnotationSource.ENSEMBL,
        dry_run_flag=False,
        update_flag=False,
        selection_ids=[1],
        taxa_id=9606,
        assembly_id=1,
        is_liftover=False,
        chromosomes={"1": 1000},
        modification_names={"a": {"short_name": "m6A", "id": 1}},
    )
    assert service.get_validated_header() == {
        "file_format": "bedRModv2",
        "taxa_id": "9606",
        "modification_type": "RNA",
        "modification_names": "a:m6A:A",
        "assembly_name": "GRCh38",
        "annotation_source": "Annotation",
        "annotation_version": "Version",
        "sequencing_platform": "Sequencing platform",
        "basecalling": "",
        "bioinformatics_workflow": "Workflow",
        "experiment": "Description of experiment.",
        "external_source": "",
    }


@pytest.mark.parametrize(
    "input_selection,check_src,exception,message",
    [
        (
            InputSelection("XXXXXXXX", [1], 1, 1, 1),
            True,
            DatasetImportError,
            "No such SMID: XXXXXXXX.",
        ),
        (
            InputSelection("12345678", [1, 99], 1, 1, 1),
            True,
            DatasetImportError,
            "No such modification ID: 99.",
        ),
        (
            InputSelection("12345678", [1], 99, 1, 1),
            True,
            DatasetImportError,
            "No such organism ID: 99.",
        ),
        (
            InputSelection("12345678", [1], 1, 99, 1),
            True,
            DatasetImportError,
            "No such technology ID: 99.",
        ),
        (
            InputSelection("12345678", [1, 1], 1, 1, 1),
            True,
            DatasetImportError,
            "Repeated modification IDs.",
        ),
        (
            InputSelection("12345678", [1], 1, 1, 99),
            True,
            DatasetImportError,
            "No such assembly ID: 99.",
        ),
        (
            InputSelection("12345678", [1], 1, 1, 2),
            True,
            DatasetImportError,
            "No such assembly GRCm38 for organism 9606.",
        ),
        (
            InputSelection("12345678", [1], 1, 1, 1),
            False,
            DatasetImportError,
            "Inconsistent source!",
        ),
    ],
)
def test_import_context_fail(
    input_selection, check_src, exception, message, Session, input_ctx
):
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session(), check_source_result=check_src)
    input_ctx["project_id"] = input_selection.project_id
    input_ctx["modification_ids"] = input_selection.modification
    input_ctx["organism_id"] = input_selection.organism
    input_ctx["technology_id"] = input_selection.technology
    input_ctx["assembly_id"] = input_selection.assembly
    with pytest.raises(exception) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert str(exc.value) == message


@pytest.mark.parametrize(
    "input_selection,regexp,replacement,exception,message",
    [
        (
            InputSelection("12345678", [1, 2], 1, 1, 1),
            r"",
            "",
            DatasetImportError,
            "Expected 'm5C' for short name; missing from 'modification_names'.",
        ),
        (
            InputSelection("12345678", [1], 1, 1, 1),
            r"#modification_names=a:m6A:A",
            "#modification_names=m:m5C:C",
            DatasetImportError,
            "Expected 'm6A' for short name; missing from 'modification_names'.",
        ),
    ],
)
def test_import_fail(
    input_selection,
    regexp,
    replacement,
    exception,
    message,
    Session,
    input_ctx,
):
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    input_ctx["project_id"] = input_selection.project_id
    input_ctx["modification_ids"] = input_selection.modification
    input_ctx["organism_id"] = input_selection.organism
    input_ctx["technology_id"] = input_selection.technology
    input_ctx["assembly_id"] = input_selection.assembly
    with pytest.raises(exception) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert str(exc.value) == message


@pytest.mark.parametrize(
    "regexp,replacement,exception,message",
    [
        (
            r"#fileformat=bedRModv2",
            "",
            SpecsError,
            "Failed to parse version from header (1).",
        ),
        (
            r"#fileformat=bedRModv2",
            r"#fileformat=bedRModvXX",
            SpecsError,
            "Failed to parse version from header (2).",
        ),
        (
            r"#fileformat=bedRModv2",
            "#fileformat=bedRModv1.8",
            SpecsError,
            "Unknown or outdated version 1.8.",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a,m6A,A",
            SpecsError,
            "Failed to parse 'modification_names' from header.",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6:A",
            SpecsError,
            "Unrecognized short name: m6.",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6A:Z",
            SpecsError,
            "Unrecognized primary base for m6A: Z. Expected A.",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6A:C",
            SpecsError,
            "Unrecognized primary base for m6A: C. Expected A.",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6A:A,b:m5C:C",
            DatasetHeaderError,
            "Modifications from header 'modification_names' ['m5C', 'm6A'] "
            "do not match the selection ['m6A'].",
        ),
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6A:A,b:m5C:A",
            SpecsError,
            "Unrecognized primary base for m5C: A. Expected C.",
        ),
        (
            r"#assembly=GRCh38",
            "",
            SpecsError,
            "Required header 'assembly' is missing.",
        ),
        (
            r"#assembly=GRCh38",
            "#assembly=",
            SpecsError,
            "Required header 'assembly' is empty.",
        ),
        (
            r"#organism=9606",
            "#organism=10090",
            DatasetHeaderError,
            "Expected 9606 for 'organism'; got 10090 from file header.",
        ),
        (
            r"#assembly=GRCh38",
            "#assembly=GRCm38",
            DatasetHeaderError,
            "Expected GRCh38 for 'assembly'; got GRCm38 from file header.",
        ),
    ],
)
def test_validate_header_fail(
    regexp,
    replacement,
    exception,
    message,
    Session,
    input_ctx,
):
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    with pytest.raises(exception) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert str(exc.value) == message


@pytest.mark.parametrize(
    "regexp,replacement",
    [
        (
            r"#modification_names=a:m6A:A",
            "#modification_names=a:m6A:a",
        ),
    ],
)
def test_validate_records(regexp, replacement, Session, input_ctx):
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)
    for record in service.get_validated_records(importer, service.get_import_context()):
        assert record == EufRecord(
            chrom="1",
            start=0,
            end=10,
            name="a",
            score=1000,
            strand=Strand.FORWARD,
            thick_start=0,
            thick_end=10,
            item_rgb="0,0,0",
            coverage=10,
            frequency=Decimal("1"),
        )


def test_validate_lifted_records(Session, input_ctx, caplog):
    # thick values are overwritten by ValidatorService._do_lift_over
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session(), is_latest_asembly=False)
    service.create_import_context(importer=importer, **input_ctx)
    for record in service.get_validated_records(importer, service.get_import_context()):
        assert record == EufRecord(
            chrom="1",
            start=10,
            end=20,
            name="a",
            score=1000,
            strand=Strand.FORWARD,
            thick_start=10,
            thick_end=20,
            item_rgb="0,0,0",
            coverage=10,
            frequency=Decimal("1"),
        )
    assert caplog.messages == [
        "Lifting over from GRCh38 to GRCh38. Overwriting thick coordinates with new start and end values."
    ]


@pytest.mark.parametrize(
    "regexp,replacement,exception,message,record_tuples",
    [
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\ta\t1000\t+\t10\t20\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Invalid coordinates: thickStart and thickEnd must be identical to chromStart and chromEnd respectively.",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Expected 11 fields, but got 10",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "",
            BedImportEmptyFile,
            "Did not find any records in 'test'",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Did not find any records in 'test'",
                )
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Unrecognized name: m6A.",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\ta,DRACH,2\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Unrecognized name: a,DRACH,2.",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t990\t1001\ta\t1000\t+\t990\t1001\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Invalid coordinates: chromEnd 1001 is greater than the size of chromosome 1.",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
        (
            "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "2\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 14: Unrecognized chrom: 2. Ignore this warning for scaffolds and contigs, otherwise this could be due to misformatting!",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Found too many errors in test (valid: 0, errors: 1)",
                ),
            ],
        ),
    ],
)
def test_validate_records_fail(
    regexp,
    replacement,
    exception,
    message,
    record_tuples,
    Session,
    input_ctx,
    caplog,
):
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)
    with pytest.raises(exception) as exc:
        for _ in service.get_validated_records(importer, service.get_import_context()):
            pass
    assert str(exc.value) == message
    assert caplog.record_tuples == record_tuples


def test_check_duplicate_dataset_fail(Session, input_ctx, dataset):  # noqa
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    input_ctx["dataset_id"] = "XXXXXXXXXXXX"
    service = _get_validator_service(Session())
    with pytest.raises(DatasetExistsError) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert (
        str(exc.value)
        == "Suspected duplicate dataset 'dataset00001' (SMID '12345678'), "
        "and title 'dataset title'."
    )


# dataset update: only the records can change

UPDATE_EUFID = "UPDATEUPDATE"
TWO_MODIFICATIONS_FILE = GOOD_EUF_FILE.replace(
    "#modification_names=a:m6A:A", "#modification_names=a:m6A:A,b:m5C:C"
)


def _add_dataset(Session, project_id, modifications, eufid=UPDATE_EUFID, **kwargs):
    # stored values identical to the header of GOOD_EUF_FILE and input_ctx,
    # unless overridden. Empty header values are stored as NULL.
    values = {
        "id": eufid,
        "project_id": project_id,
        "title": "dataset title",
        "organism_id": 1,
        "technology_id": 1,
        "date_added": datetime(2024, 10, 21, 8, 10, 27),
        "modification_type": "RNA",
        "sequencing_platform": "Sequencing platform",
        "basecalling": None,
        "bioinformatics_workflow": "Workflow",
        "experiment": "Description of experiment.",
        "external_source": None,
    }
    values.update(kwargs)
    with Session() as session:
        session.add(Dataset(**values))
        for mid in modifications:
            session.add(
                DatasetModificationAssociation(dataset_id=eufid, modification_id=mid)
            )
        session.commit()


def _update(Session, input_ctx, euf_file=GOOD_EUF_FILE, **kwargs):
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    input_ctx.update({"dataset_id": UPDATE_EUFID, "update_flag": True, **kwargs})
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)
    return service


def test_update_identical_metadata(Session, input_ctx):
    _add_dataset(Session, input_ctx["project_id"], [1])
    service = _update(Session, input_ctx)
    context = service.get_import_context()
    assert context.update_flag is True
    assert context.dataset_id == UPDATE_EUFID


def test_update_identical_metadata_two_modifications(Session, input_ctx):
    _add_dataset(Session, input_ctx["project_id"], [1, 2])
    _update(
        Session, input_ctx, euf_file=TWO_MODIFICATIONS_FILE, modification_ids=[1, 2]
    )


def test_update_with_similar_dataset(Session, input_ctx):
    # same metadata, other modification: no ambiguity
    _add_dataset(Session, input_ctx["project_id"], [1])
    _add_dataset(Session, input_ctx["project_id"], [2], eufid="OTHEROTHEROT")
    _update(Session, input_ctx)


@pytest.mark.parametrize(
    "stored_modifications,header,modification_ids,message",
    [
        # more modifications
        (
            [1],
            TWO_MODIFICATIONS_FILE,
            [1, 2],
            "modifications: Dataset has '[1]', got '[1, 2]'",
        ),
        # fewer modifications
        (
            [1, 2],
            GOOD_EUF_FILE,
            [1],
            "modifications: Dataset has '[1, 2]', got '[1]'",
        ),
        # different modification
        (
            [2],
            GOOD_EUF_FILE,
            [1],
            "modifications: Dataset has '[2]', got '[1]'",
        ),
    ],
)
def test_update_fail_modifications(
    stored_modifications, header, modification_ids, message, Session, input_ctx
):
    _add_dataset(Session, input_ctx["project_id"], stored_modifications)
    with pytest.raises(DatasetUpdateError) as exc:
        _update(Session, input_ctx, euf_file=header, modification_ids=modification_ids)
    assert f"Cannot update records for dataset '{UPDATE_EUFID}'." in str(exc.value)
    assert message in str(exc.value)


@pytest.mark.parametrize(
    "stored,message",
    [
        (
            {"title": "other title"},
            "title: Dataset has 'other title', got 'dataset title'",
        ),
        ({"technology_id": 2}, "technology_id: Dataset has '2', got '1'"),
        ({"organism_id": 2}, "organism_id: Dataset has '2', got '1'"),
        # (
        #     {"modification_type": "DNA"},
        #     "header 'modification_type': Dataset has 'DNA', got 'RNA'",
        # ),
        (
            {"sequencing_platform": "Other platform"},
            "sequencing_platform: Dataset has 'Other platform', got 'Sequencing platform'",
        ),
        ({"basecalling": "bc"}, "basecalling: Dataset has 'bc', got ''"),
        (
            {"bioinformatics_workflow": None},
            "bioinformatics_workflow: Dataset has '', got 'Workflow'",
        ),
        (
            {"experiment": "Other"},
            "experiment: Dataset has 'Other', got 'Description of experiment.'",
        ),
        (
            {"external_source": "GEO"},
            "external_source: Dataset has 'GEO', got ''",
        ),
    ],
)
def test_update_fail_metadata(stored, message, Session, input_ctx):
    _add_dataset(Session, input_ctx["project_id"], [1], **stored)
    with pytest.raises(DatasetUpdateError) as exc:
        _update(Session, input_ctx)
    assert message in str(exc.value)


def test_update_fail_project(Session, input_ctx, project):  # noqa
    # second project of the fixture
    _add_dataset(Session, "ABCDEFGH", [1])
    with pytest.raises(DatasetUpdateError) as exc:
        _update(Session, input_ctx)
    assert "project_id: Dataset has 'ABCDEFGH', got '12345678'" in str(exc.value)


def test_update_fail_reports_all_mismatches(Session, input_ctx):
    _add_dataset(
        Session,
        input_ctx["project_id"],
        [1, 2],
        title="other title",
        experiment="Other",
    )
    with pytest.raises(DatasetUpdateError) as exc:
        _update(Session, input_ctx)
    message = str(exc.value)
    assert "title: Dataset has 'other title'" in message
    assert "modifications: Dataset has '[1, 2]', got '[1]'" in message
    assert "experiment: Dataset has 'Other'" in message


def test_update_fail_no_such_dataset(Session, input_ctx):
    with pytest.raises(DatasetUpdateError) as exc:
        _update(Session, input_ctx)
    assert str(exc.value) == f"No such dataset: '{UPDATE_EUFID}'."


def test_update_checks_do_not_apply_to_new_dataset(Session, input_ctx):
    # a different header is fine for a new dataset
    _add_dataset(Session, input_ctx["project_id"], [1], title="other title")
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)


def test_selection_not_found(Session, input_ctx):
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    input_ctx["organism_id"] = 2
    service = _get_validator_service(Session())
    with pytest.raises(SelectionNotFoundError) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert (
        str(exc.value)
        == "Selection with m6A, Cell type 2, and Technology 1 (9606) not found."
    )


@pytest.mark.parametrize(
    "primary_base,reference_base,valid",
    [
        ("A", "A", True),
        ("a", "A", True),
        ("C", "A", False),
        ("U", "U", True),
        ("T", "U", True),
        ("t", "U", True),
        ("A", "U", False),
        ("T", "A", False),
        ("Z", "A", False),
        # reference base other than A, C, G, U: MODOMICS is the reference
        ("A", "X", True),
        ("Z", "N", False),
    ],
)
def test_is_valid_primary_base(primary_base, reference_base, valid):
    all_bases = {"A", "C", "G", "U", "X", "QtRNA"}
    assert (
        ValidatorService._is_valid_primary_base(primary_base, reference_base, all_bases)
        is valid
    )


def test_validate_records_end_equal_to_chrom_size(Session, input_ctx):
    euf_file = GOOD_EUF_FILE.replace(
        "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
        "1\t990\t1000\ta\t1000\t+\t990\t1000\t0,0,0\t10\t1",
    )
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    service.create_import_context(importer=importer, **input_ctx)
    records = list(
        service.get_validated_records(importer, service.get_import_context())
    )
    assert [(r.start, r.end) for r in records] == [(990, 1000)]


def test_validate_records_range_is_not_checked_before_liftover(Session, input_ctx):
    # coordinates are those of the original assembly: sizes are unknown
    euf_file = GOOD_EUF_FILE.replace(
        "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
        "1\t5000\t5010\ta\t1000\t+\t5000\t5010\t0,0,0\t10\t1",
    )
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session(), is_latest_asembly=False)
    raw_records = []

    def create_temp_euf_file(records):
        # the mock does not read the records
        raw_records.extend(records)
        return "xxx"

    service._bedtools_service.create_temp_euf_file = create_temp_euf_file
    service.create_import_context(importer=importer, **input_ctx)
    records = list(
        service.get_validated_records(importer, service.get_import_context())
    )
    assert [(r.start, r.end) for r in raw_records] == [(5000, 5010)]  # not rejected
    assert [(r.start, r.end) for r in records] == [(10, 20)]  # mock: lifted record


def test_read_only_context_checks_range(Session, setup):  # noqa
    # comparison view: same checks, header modifications as declared
    euf_file = GOOD_EUF_FILE.replace(
        "1\t0\t10\ta\t1000\t+\t0\t10\t0,0,0\t10\t1",
        "1\t990\t1001\ta\t1000\t+\t990\t1001\t0,0,0\t10\t1",
    )
    importer = EufImporter(stream=StringIO(euf_file), source="test")
    service = _get_validator_service(Session())
    service.create_read_only_import_context(importer=importer, taxa_id=9606)
    with pytest.raises(BedImportTooManyErrors):
        list(service.get_validated_records(importer, service.get_read_only_context()))
