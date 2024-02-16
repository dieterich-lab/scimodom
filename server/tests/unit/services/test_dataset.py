from datetime import datetime, timezone
from io import StringIO

import pytest
from sqlalchemy import select, func

from scimodom.database.models import (
    # Assembly,
    Association,
    Selection,
    Dataset,
    Modification,
    DetectionTechnology,
    Organism,
    Project,
    ProjectSource,
    ProjectContact,
)
import scimodom.database.queries as queries
from scimodom.services.dataset import DataService, InstantiationError, DatasetError
from scimodom.services.project import ProjectService
import scimodom.utils.utils as utils


# NOTE: force add project directly to avoid using ProjectService


# def _get_file(EUF_version):
#     string = f"""#fileformat=bedRModv{EUF_version}
#     #organism=9606
#     #modification_type=RNA
#     #assembly=GRCh38
#     #annotation_source=Annotation
#     #annotation_version=Version
#     #sequencing_platform=Sequencing platform
#     #basecalling=
#     #bioinformatics_workflow=Workflow
#     #experiment=Description of experiment.
#     #external_source=
#     #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
#     1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10
#     1\t139220\t139221\tm5C\t5\t+\t139220\t139221\t0,0,0\t100\t5
#     1\t139221\t139222\tm5C\t5\t+\t139221\t139222\t0,0,0\t300\t5
#     1\t139222\t139223\tm6A\t500\t+\t139222\t139223\t0,0,0\t250\t100
#     1\t139223\t139224\tm6A\t5\t+\t139223\t139224\t0,0,0\t10\t5"""
#     return StringIO(string)


# def _get_project(project_template, case=None):
#     # set selection 2 to m5C, but same cell type as 1
#     project = project_template.copy()
#     if case == "two":
#         project["metadata"][1]["modomics_id"] = "2000000005C"
#         project["metadata"][1]["organism"]["cto"] = "Cell Type 1"
#     return project


def _add_selection(session, metadata):
    for d in utils.to_list(metadata):
        rna = d["rna"]
        modomics_id = d["modomics_id"]
        query = queries.query_column_where(
            Modification, "id", filters={"rna": rna, "modomics_id": modomics_id}
        )
        modification_id = session.execute(query).scalar()
        if not modification_id:
            modification = Modification(rna=rna, modomics_id=modomics_id)
            session.add(modification)
            session.flush()
            modification_id = modification.id

        tech = d["tech"]
        method_id = d["method_id"]
        query = queries.query_column_where(
            DetectionTechnology,
            "id",
            filters={"tech": tech, "method_id": method_id},
        )
        technology_id = session.execute(query).scalar()
        if not technology_id:
            technology = DetectionTechnology(tech=tech, method_id=method_id)
            session.add(technology)
            session.flush()
            technology_id = technology.id

        d_organism = d["organism"]
        cto = d_organism["cto"]
        taxa_id = d_organism["taxa_id"]
        query = queries.query_column_where(
            Organism, "id", filters={"cto": cto, "taxa_id": taxa_id}
        )
        organism_id = session.execute(query).scalar()
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


def test_instantiation_from_selection_no_smid_fail(Session):
    with pytest.raises(InstantiationError) as exc:
        DataService.from_selection(
            session=Session(),
            smid="12345678",
            title="title",
            filen="filen",
            assembly_id=1,
            selection_id=[1, 1],
        )
    assert (
        str(exc.value) == "Unrecognised SMID 12345678. Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


def test_instantiation_from_new_no_smid_fail(Session):
    with pytest.raises(InstantiationError) as exc:
        DataService.from_new(
            session=Session(),
            smid="12345678",
            title="title",
            filen="filen",
            assembly_id=1,
            modification_id=1,
            technology_id=1,
            organism_id=1,
        )
    assert (
        str(exc.value) == "Unrecognised SMID 12345678. Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


def test_instantiation_from_selection_fail(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService.from_selection(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            selection_id=[1, 1],
        )
    assert str(exc.value) == "Repeated selection IDs. Cannot instantiate DataService!"
    assert exc.type == InstantiationError


def test_instantiation_from_new_fail(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService.from_new(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_id=[1, 1],
            technology_id=1,
            organism_id=1,
        )
    assert (
        str(exc.value) == "Repeated modification IDs. Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


def test_from_new_fail_no_row(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService.from_new(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_id=2,
            technology_id=2,
            organism_id=1,
        )
    assert (
        str(exc.value)
        == "Selection (mod=2, tech=2, organism=1) does not exists. Aborting transaction!"
    )
    assert exc.type == InstantiationError


def test_from_selection_fail(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(ValueError) as exc:
        DataService.from_selection(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            selection_id=99,
        )
    assert str(exc.value) == "Selection ID = 99 not found! Aborting transaction!"
    assert exc.type == ValueError


@pytest.mark.parametrize(
    "modid,techid,orgid,name",
    [
        (99, 1, 1, "Modification"),
        (1, 99, 1, "Technology"),
        (1, 1, 99, "Organism"),
    ],
)
def test_from_new_fail(modid, techid, orgid, name, Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(ValueError) as exc:
        DataService.from_new(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_id=modid,
            technology_id=techid,
            organism_id=orgid,
        )
    assert str(exc.value) == f"{name} ID = 99 not found! Aborting transaction!"
    assert exc.type == ValueError


@pytest.mark.parametrize(
    "selid,name",
    [
        (2, "organism"),
        (3, "technology"),
    ],
)
def test_ids_fail(selid, name, Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService.from_selection(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            selection_id=[1, selid],
        )
    assert (
        str(exc.value)
        == f"Two different {name} IDs 1 and 2 are associated with this dataset. Aborting transaction!"
    )
    assert exc.type == InstantiationError


def test_from_new(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    service = DataService.from_new(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        modification_id=1,
        technology_id=1,
        organism_id=1,
    )
    assert service._selection_id[0] == 1
    assert len(service._selection_id) == 1
    # with Session() as session, session.begin():
    #     stmt = select(func.count()).select_from(Dataset)
    #     num_records = session.execute(stmt).scalar()
    #     assert num_records == 0


def test_from_selection(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    service = DataService.from_selection(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        selection_id=1,
    )
    assert service._modification_id[0] == 1
    assert len(service._modification_id) == 1
    assert service._technology_id == 1
    assert service._organism_id == 1


def test_validate_entry(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()

    service = DataService.from_selection(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        selection_id=1,
    )
    assert service._validate_entry() is None


def test_validate_existing_entry(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        # force/add dataset manually
        dataset = Dataset(
            id="123456789ABC",
            project_id=smid,
            title="title",
            modification_type="RNA",
        )
        association = Association(dataset_id="123456789ABC", selection_id=1)
        session.add_all([dataset, association])
        session.commit()

    service = DataService.from_selection(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        selection_id=1,
    )
    with pytest.raises(DatasetError) as exc:
        service._validate_entry()
    assert str(exc.value) == (
        "A similar record with EUFID = 123456789ABC already exists for "
        f"project {smid} with title = title, and the following selection ID 1. "
        "Aborting transaction!"
    )
    assert exc.type == DatasetError


def test_add_association(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)

    service = DataService.from_selection(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        selection_id=[1, 4],
    )
    service._create_eufid()
    service._add_association()
    expected_association = {"m6A": 1, "m5C": 2}
    assert service._association == expected_association


# ------------------------

# @pytest.mark.parametrize(
#     "selection",
#     [
#         ("one"),
#         ("two"),
#         ("none"),
#     ],
# )
# def test_dataset_get_selection(selection, Session, setup, project_template, caplog):
#     project = _get_project(project_template, case=selection)

#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project)
#         session.commit()

#     modification_ids = [1, 2]
#     if selection == "one":
#         _ = modification_ids.pop(1)
#     taxa_id = 9606
#     assembly_id = 1
#     technology_id = 1
#     organism_id = 1

#     service = DataService(
#         Session(),
#         smid,
#         "Dataset title",
#         "filename",
#         StringIO("filename"),
#         taxa_id,
#         assembly_id,
#         modification_ids,
#         technology_id,
#         organism_id,
#     )
#     # for some cases we have "sqlalchemy.exc.NoResultFound: No row was found when one was required"
#     # that "bypasses" the except?
#     if selection == "none":
#         with pytest.raises(Exception) as excinfo:
#             service._get_selection()
#         # assert caplog.record_tuples == [('scimodom.services.dataset', 40, 'Selection for m5C (mRNA), Technology 1, and Cell Type 1 not found! This is likely due to database corruption or a bug.')]
#     else:
#         service._get_selection()


# def test_dataset_validate_assembly(Session, setup, project_template):
#     taxa_id = 9606
#     modification_ids = [1]
#     technology_id = 1
#     organism_id = 1

#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         assembly = Assembly(name="GRCh19", taxa_id=taxa_id, version="123456789ABC")
#         session.add(assembly)
#         session.flush()
#         query = queries.query_column_where("Assembly", "id", filters={"name": "GRCh19"})
#         assembly_id = session.execute(query).scalar()
#         session.commit()

#     service = DataService(
#         Session(),
#         smid,
#         "Dataset title",
#         "filename",
#         StringIO("filename"),
#         taxa_id,
#         assembly_id,
#         modification_ids,
#         technology_id,
#         organism_id,
#     )
#     service._validate_assembly()
#     assert service._lifted is True


# @pytest.mark.parametrize(
#     "selection",
#     [
#         ("one"),
#         ("two"),
#     ],
# )
# def test_dataset_create_eufid(
#     selection, Session, setup, project_template, caplog, EUF_version, data_path
# ):
#     # two modifications for the same dataset, same technology, same organism
#     project = _get_project(project_template, case=selection)

#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project)
#         session.commit()

#     taxa_id = 9606
#     assembly_id = 1  # GRCh38
#     modification_ids = [1, 2]
#     if selection == "one":
#         _ = modification_ids.pop(1)
#     technology_id = 1
#     organism_id = 1  # Homo sapiens

#     service = DataService(
#         Session(),
#         smid,
#         "Dataset title",
#         "filename",
#         _get_file(EUF_version),
#         taxa_id,
#         assembly_id,
#         modification_ids,
#         technology_id,
#         organism_id,
#     )
#     service._get_selection()
#     if selection == "one":
#         with pytest.raises(Exception) as excinfo:
#             service._create_eufid()
#         # assert caplog.record_tuples == [('scimodom.services.importer', 30, 'Overwriting header: assembly=GRCh38 from filename with GRCh38 given at upload. Data import will continue...'), ('scimodom.services.dataset', 40, "Selection for modification and modifications read from filename differ: {'m5c'}. Aborting transaction!")]
#     else:
#         service._create_eufid()


# def test_dataset_add_association(Session, setup, project_template):
#     with Session() as session, session.begin():
#         session.add_all(setup)
#         smid = _mock_project_service(session, project_template)
#         session.commit()

#     taxa_id = 9606
#     assembly_id = 1
#     modification_ids = [1]
#     technology_id = 1
#     organism_id = 1

#     service = DataService(
#         Session(),
#         smid,
#         "Dataset title",
#         "filename",
#         StringIO("filename"),
#         taxa_id,
#         assembly_id,
#         modification_ids,
#         technology_id,
#         organism_id,
#     )
#     service._get_selection()
#     service._eufid = "123456789ABC"
#     service._add_association()

#     with Session() as session, session.begin():
#         records = session.execute(select(Association)).scalar()
#         assert records.id == 1
#         assert records.dataset_id == "123456789ABC"
#         assert records.selection_id == 1
#         records = session.execute(select(Selection)).scalar()
#         assert records.id == 1
#         assert records.modification_id == modification_ids[0]
#         assert records.technology_id == technology_id
#         assert records.organism_id == organism_id
