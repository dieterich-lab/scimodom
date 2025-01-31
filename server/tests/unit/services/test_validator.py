from collections import defaultdict, namedtuple
from io import StringIO

import pytest
from sqlalchemy.exc import NoResultFound

from scimodom.database.models import Assembly
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
from scimodom.utils.specs.enums import AnnotationSource, ImportLimits


InputSelection = namedtuple(
    "InputSelection", "smid modification organism technology assembly"
)


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

    def get_seqids(self, taxa_id: int) -> list[str]:  # noqa
        return ["1"]

    def get_name_for_version(self, taxa_id: int) -> str:  # noqa
        return "GRCh38"

    def create_lifted_file(
        self,
        assembly: Assembly,
        raw_file: str,
        unmapped_file: str | None = None,
        threshold: float = ImportLimits.LIFTOVER.max,
    ) -> StringIO:  # noqa
        s = StringIO(GOOD_EUF_FILE)
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
        "smid": project[0].id,
        "eufid": "NEWNEWNEWNEW",
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


def test_read_only_import_context(Session, setup):  # noqa
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session())
    service.create_read_only_import_context(importer=importer, taxa_id=9606)
    assert service.get_read_only_context() == _ReadOnlyImportContext(
        taxa_id=9606,
        assembly_id=1,
        is_liftover=False,
        seqids=["1"],
        modification_names={"Y": hash("Y"), "m5C": hash("m5C"), "m6A": hash("m6A")},
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
        seqids=["1"],
        modification_names={"Y": hash("Y"), "m5C": hash("m5C"), "m6A": hash("m6A")},
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
        smid="12345678",
        eufid="NEWNEWNEWNEW",
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
        seqids=["1"],
        modification_names={"m6A": 1},
    )
    assert service.get_validated_header() == {
        "file_format": "bedRModv1.8",
        "taxa_id": "9606",
        "modification_type": "RNA",
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
    input_ctx["smid"] = input_selection.smid
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
            r"#fileformat=bedRModv1.8",
            "",
            SpecsError,
            "Failed to parse version from header (1).",
        ),
        (
            r"#fileformat=bedRModv1.8",
            r"#fileformat=bedRModvXX",
            SpecsError,
            "Failed to parse version from header (2).",
        ),
        (
            r"#fileformat=bedRModv1.8",
            "#fileformat=bedRModv1.6",
            SpecsError,
            "Unknown or outdated version 1.6.",
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


@pytest.mark.parametrize("liftover", (False, True))
def test_validate_records(liftover, Session, input_ctx):
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    service = _get_validator_service(Session(), is_latest_asembly=liftover)
    service.create_import_context(importer=importer, **input_ctx)
    for _ in service.get_validated_records(importer, service.get_import_context()):
        pass


@pytest.mark.parametrize(
    "regexp,replacement,exception,message,record_tuples",
    [
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 13: Expected 11 fields, but got 10",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
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
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    40,
                    "Did not find any records in 'test'",
                )
            ],
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors in test (valid: 0, errors: 1)",
            [
                (
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 13: Unrecognized name: m6.",
                ),
                (
                    "scimodom.utils.importer.bed_importer",
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
                    "scimodom.utils.importer.bed_importer",
                    30,
                    "test, line 13: Unrecognized chrom: 2. Ignore this warning for scaffolds and contigs, otherwise this could be due to misformatting!",
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


@pytest.mark.parametrize(
    "eufid,update,exception,message",
    [
        (
            "XXXXXXXXXXXX",
            False,
            DatasetExistsError,
            "Suspected duplicate dataset 'dataset_id01' (SMID '12345678'), and title 'dataset title'.",
        ),
        (
            "dataset_id02",
            True,
            DatasetUpdateError,
            "Provided dataset 'dataset_id02', but found 'dataset_id01' with title 'dataset title' (SMID '12345678').",
        ),
    ],
)
def test_check_duplicate_dataset_fail(
    eufid, update, exception, message, Session, input_ctx, dataset
):  # noqa
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    input_ctx["eufid"] = eufid
    input_ctx["update_flag"] = update
    service = _get_validator_service(Session())
    with pytest.raises(exception) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert str(exc.value) == message
    assert exc.type == exception


def test_selection_not_found(Session, input_ctx):
    importer = EufImporter(stream=StringIO(GOOD_EUF_FILE), source="test")
    input_ctx["organism_id"] = 2
    service = _get_validator_service(Session())
    with pytest.raises(SelectionNotFoundError) as exc:
        service.create_import_context(importer=importer, **input_ctx)
    assert (
        str(exc.value)
        == "No such selection with m6A, Technology 1, and Cell type 2 (9606)."
    )
