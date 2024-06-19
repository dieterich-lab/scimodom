from datetime import datetime, timezone
from io import StringIO
from os import makedirs

import pytest
from sqlalchemy import select

import scimodom.utils.utils as utils
from scimodom.database.models import (
    Selection,
    Dataset,
    Modification,
    DetectionTechnology,
    Organism,
    Project,
    ProjectSource,
    ProjectContact,
    Assembly,
    Data,
)
from scimodom.services.annotation import AnnotationSource
from scimodom.services.dataset import (
    DatasetService,
    SpecsError,
    DatasetHeaderError,
)
from scimodom.services.project import ProjectService
from scimodom.utils.bed_importer import BedImportEmptyFile, BedImportTooManyErrors


# NOTE: force add project directly to avoid using ProjectService


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


def get_dataset_service(
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
        bedtools_service=MockBedToolsService(),  # noqa
        assembly_service=MockAssemblyService(
            is_latest=is_latest_asembly, assemblies_by_id=assemblies_by_id
        ),  # noqa
        annotation_service=MockAnnotationService(
            check_source_result=check_source_result
        ),  # noqa
    )


def _get_dataset_service(dependencies):
    return DatasetService(
        dependencies.Session(),
        bedtools_service=dependencies.bedtools_service,
        assembly_service=dependencies.assembly_service,
        annotation_service=dependencies.annotation_service,
    )


def _add_selection(session, metadata):
    for d in utils.to_list(metadata):
        rna = d["rna"]
        modomics_id = d["modomics_id"]
        modification_id = session.execute(
            select(Modification.id).filter_by(modomics_id=modomics_id, rna=rna)
        ).scalar()  # scalar_one() ??
        if not modification_id:
            modification = Modification(rna=rna, modomics_id=modomics_id)
            session.add(modification)
            session.flush()
            modification_id = modification.id

        tech = d["tech"]
        method_id = d["method_id"]
        technology_id = session.execute(
            select(DetectionTechnology.id).filter_by(method_id=method_id, tech=tech)
        ).scalar()  # .scalar_one()
        if not technology_id:
            technology = DetectionTechnology(tech=tech, method_id=method_id)
            session.add(technology)
            session.flush()
            technology_id = technology.id

        d_organism = d["organism"]
        cto = d_organism["cto"]
        taxa_id = d_organism["taxa_id"]
        organism_id = session.execute(
            select(Organism.id).filter_by(taxa_id=taxa_id, cto=cto)
        ).scalar()  # .scalar_one()
        if not organism_id:
            organism = Organism(cto=cto, taxa_id=taxa_id)
            session.add(organism)
            session.flush()
            organism_id = organism.id

        selection = Selection(
            modification_id=modification_id,
            technology_id=technology_id,
            organism_id=organism_id,
        )
        session.add(selection)
        session.flush()


def _add_contact(session, project):
    contact_name = project["contact_name"]
    contact_institution = project["contact_institution"]
    contact_email = project["contact_email"]
    contact = ProjectContact(
        contact_name=contact_name,
        contact_institution=contact_institution,
        contact_email=contact_email,
    )
    session.add(contact)
    session.flush()
    contact_id = contact.id
    return contact_id


def _mock_project_service(session, project):
    _add_selection(session, project["metadata"])
    contact_id = _add_contact(session, project)
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    smid = utils.gen_short_uuid(ProjectService.SMID_LENGTH, [])
    project_tbl = Project(
        id=smid,
        title=project["title"],
        summary=project["summary"],
        contact_id=contact_id,
        date_published=datetime.fromisoformat(project["date_published"]),
        date_added=stamp,
    )
    sources = [project_tbl]
    for s in utils.to_list(project["external_sources"]):
        source = ProjectSource(project_id=smid, doi=s["doi"], pmid=s["pmid"])
        sources.append(source)

    session.add_all(sources)
    return smid


@pytest.fixture
def project(Session, setup, project_template):  # noqa
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    yield smid


@pytest.fixture
def chrome_file(data_path):
    path = f"{data_path.ASSEMBLY_PATH}/Homo_sapiens/GRCh38/"
    makedirs(path, exist_ok=True)
    with open(f"{path}/chrom.sizes", "w") as chrom_file:
        chrom_file.write("1\t248956422\n")


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
    regexp, replacement, Session, project, freezer, chrome_file
):  # noqa
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    service = get_dataset_service(Session())
    file = StringIO(euf_file)
    freezer.move_to("2017-05-20 11:00:23")
    eufid = service.import_dataset(
        file,
        source="test",
        smid=project,
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
        assert dataset.project_id == project
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
        assert data[0].strand == "+"


@pytest.mark.parametrize(
    "regexp,replacement,exception,message",
    [
        (
            r"#fileformat=bedRModv1.7",
            "",
            SpecsError,
            "Failed to parse version from header (1).",
        ),
        (
            r"#fileformat=bedRModv1.7",
            r"#fileformat=bedRModvXX",
            SpecsError,
            "Failed to parse version from header (2).",
        ),
        (
            r"#fileformat=bedRModv1.7",
            "#fileformat=bedRModv2.1",
            SpecsError,
            "Unknown or outdated version 2.1.",
        ),
        (r"#assembly=GRCh38", "", SpecsError, "Required header 'assembly' is missing."),
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
            "Expected 9606 for organism; got 10090 from file header.",
        ),
        (
            r"#assembly=GRCh38",
            "#assembly=GRCm38",
            DatasetHeaderError,
            "Expected GRCh38 for assembly; got GRCm38 from file header.",
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10",
            BedImportTooManyErrors,
            "Found too many errors ins 'test' (valid: 0, errors: 1)",
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "",
            BedImportEmptyFile,
            "Did not find any records in 'test'",
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "1\t0\t10\tm6\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors ins 'test' (valid: 0, errors: 1)",
        ),
        (
            "1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            "2\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1",
            BedImportTooManyErrors,
            "Found too many errors ins 'test' (valid: 0, errors: 1)",
        ),
    ],
)
def test_bad_import(
    regexp, replacement, exception, message, Session, project, freezer, chrome_file
):  # noqa
    euf_file = GOOD_EUF_FILE.replace(regexp, replacement)
    service = get_dataset_service(Session())
    file = StringIO(euf_file)
    freezer.move_to("2017-05-20 11:00:23")
    with pytest.raises(exception) as exc:
        service.import_dataset(
            file,
            source="test",
            smid=project,
            title="title",
            assembly_id=1,
            modification_ids=[1],
            technology_id=1,
            organism_id=1,
            annotation_source=AnnotationSource.ENSEMBL,
        )
    assert str(exc.value) == message


# def test_validate_imported_fail():
#     with pytest.raises(DatasetHeaderError) as exc:
#         DataService.validate_imported("test", "a", "b")
#     assert (
#         str(exc.value)
#         == "Expected a for test; got b (file header). Aborting transaction!"
#     )
#     assert exc.type == DatasetHeaderError
#
#
# def test_validate_imported():
#     assert DataService.validate_imported("test", "a", "a") is None
#
#
# def test_validate_args_no_smid(Session):
#     with pytest.raises(InstantiationError) as exc:
#         DataService(
#             session=Session(),
#             smid="12345678",
#             title="title",
#             filen="filen",
#             assembly_id=1,
#             modification_ids=1,
#             technology_id=1,
#             organism_id=1,
#         )
#     assert (
#         str(exc.value) == "Unrecognised SMID 12345678. Cannot instantiate DataService!"
#     )
#     assert exc.type == InstantiationError
#
#
# def test_validate_args_repeated(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()
#     with pytest.raises(InstantiationError) as exc:
#         DataService(
#             session=Session(),
#             smid=smid,
#             title="title",
#             filen="filen",
#             assembly_id=1,
#             modification_ids=[1, 1],
#             technology_id=1,
#             organism_id=1,
#         )
#     assert (
#         str(exc.value) == "Repeated modification IDs. Cannot instantiate DataService!"
#     )
#     assert exc.type == InstantiationError
#
#
# @pytest.mark.parametrize(
#     "modid,techid,orgid,name",
#     [
#         (99, 1, 1, "Modification"),
#         (1, 99, 1, "Technology"),
#         (1, 1, 99, "Organism"),
#     ],
# )
# def test_validate_args_fail(
#     modid, techid, orgid, name, Session, setup, project_template
# ):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()
#     with pytest.raises(InstantiationError) as exc:
#         DataService(
#             session=Session(),
#             smid=smid,
#             title="title",
#             filen="filen",
#             assembly_id=1,
#             modification_ids=modid,
#             technology_id=techid,
#             organism_id=orgid,
#         )
#     assert (
#         str(exc.value) == f"{name} ID = 99 not found! Cannot instantiate DataService!"
#     )
#     assert exc.type == InstantiationError
#
#
# def test_validate_selection_ids_fail(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()
#     with pytest.raises(SelectionNotFoundError) as exc:
#         DataService(
#             session=Session(),
#             smid=smid,
#             title="title",
#             filen="filen",
#             assembly_id=1,
#             modification_ids=2,
#             technology_id=2,
#             organism_id=1,
#         )
#     assert (
#         str(exc.value)
#         == "Selection (mod=m5C, tech=Technology 2, organism=(Homo sapiens, Cell Type 1)) does not exists. Aborting transaction!"
#     )
#     assert exc.type == SelectionNotFoundError
#
#
# def test_instantiation(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()
#     service = DataService(
#         session=Session(),
#         smid=smid,
#         title="title",
#         filen="filen",
#         assembly_id=1,
#         modification_ids=1,
#         technology_id=1,
#         organism_id=1,
#     )
#     assert service._assembly_name == "GRCh38"
#     assert service._current_assembly_name == "GRCh38"
#     assert service._organism_name == "Homo sapiens"
#     assert service._taxa_id == 9606
#     assert service._selection_ids == [1]
#     assert service._modification_names == {"m6A": 1}
#
#
# def test_validate_entry(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()
#
#     service = DataService(
#         session=Session(),
#         smid=smid,
#         title="title",
#         filen="filen",
#         assembly_id=1,
#         modification_ids=1,
#         technology_id=1,
#         organism_id=1,
#     )
#     assert service._validate_entry() is None
#
#
# def test_validate_existing_entry(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         # force/add dataset manually
#         stamp = datetime.now(timezone.utc).replace(microsecond=0)
#         dataset = Dataset(
#             id="123456789ABC",
#             project_id=smid,
#             organism_id=1,
#             technology_id=1,
#             title="title",
#             modification_type="RNA",
#             date_added=stamp,
#         )
#         association = DatasetModificationAssociation(
#             dataset_id="123456789ABC", modification_id=1
#         )
#         session.add_all([dataset, association])
#         session.commit()
#
#     service = DataService(
#         session=Session(),
#         smid=smid,
#         title="title",
#         filen="filen",
#         assembly_id=1,
#         modification_ids=1,
#         technology_id=1,
#         organism_id=1,
#     )
#     with pytest.raises(DatasetExistsError) as exc:
#         service._validate_entry()
#     assert str(exc.value) == (
#         "Suspected duplicate record with EUFID = 123456789ABC "
#         f"(SMID = {smid}), and title = title. Aborting transaction!"
#     )
#     assert exc.type == DatasetExistsError
#
#
# def test_add_association(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#
#     service = DataService(
#         session=Session(),
#         smid=smid,
#         title="title",
#         filen="filen",
#         assembly_id=1,
#         modification_ids=[1, 2],
#         technology_id=1,
#         organism_id=1,
#     )
#     service._create_eufid()
#     service._add_association()
#     assert service._selection_ids == [1, 4]
#     assert service._modification_names == {"m6A": 1, "m5C": 2}
#     assert service.get_eufid() == service._eufid
