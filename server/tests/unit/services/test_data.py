from datetime import datetime, timezone
from io import StringIO

import pytest
from sqlalchemy import select, func

from scimodom.database.models import (
    DatasetModificationAssociation,
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
from scimodom.services.data import (
    DataService,
    InstantiationError,
    SelectionExistsError,
    DatasetExistsError,
    DatasetHeaderError,
)
from scimodom.services.project import ProjectService
import scimodom.utils.utils as utils


# NOTE: force add project directly to avoid using ProjectService


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


def test_validate_imported_fail():
    with pytest.raises(DatasetHeaderError) as exc:
        DataService.validate_imported("test", "a", "b")
    assert (
        str(exc.value)
        == "Expected a for test; got b (file header). Aborting transaction!"
    )
    assert exc.type == DatasetHeaderError


def test_validate_imported():
    assert DataService.validate_imported("test", "a", "a") is None


def test_validate_args_no_smid(Session):
    with pytest.raises(InstantiationError) as exc:
        DataService(
            session=Session(),
            smid="12345678",
            title="title",
            filen="filen",
            assembly_id=1,
            modification_ids=1,
            technology_id=1,
            organism_id=1,
        )
    assert (
        str(exc.value) == "Unrecognised SMID 12345678. Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


def test_validate_args_repeated(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_ids=[1, 1],
            technology_id=1,
            organism_id=1,
        )
    assert (
        str(exc.value) == "Repeated modification IDs. Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


@pytest.mark.parametrize(
    "modid,techid,orgid,name",
    [
        (99, 1, 1, "Modification"),
        (1, 99, 1, "Technology"),
        (1, 1, 99, "Organism"),
    ],
)
def test_validate_args_fail(
    modid, techid, orgid, name, Session, setup, project_template
):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(InstantiationError) as exc:
        DataService(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_ids=modid,
            technology_id=techid,
            organism_id=orgid,
        )
    assert (
        str(exc.value) == f"{name} ID = 99 not found! Cannot instantiate DataService!"
    )
    assert exc.type == InstantiationError


def test_validate_selection_ids_fail(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    with pytest.raises(SelectionExistsError) as exc:
        DataService(
            session=Session(),
            smid=smid,
            title="title",
            filen="filen",
            assembly_id=1,
            modification_ids=2,
            technology_id=2,
            organism_id=1,
        )
    assert (
        str(exc.value)
        == "Selection (mod=m5C, tech=Technology 2, organism=(Homo sapiens, Cell Type 1)) does not exists. Aborting transaction!"
    )
    assert exc.type == SelectionExistsError


def test_instantiation(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()
    service = DataService(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        modification_ids=1,
        technology_id=1,
        organism_id=1,
    )
    assert service._assembly_name == "GRCh38"
    assert service._current_assembly_name == "GRCh38"
    assert service._organism_name == "Homo sapiens"
    assert service._taxa_id == 9606
    assert service._selection_ids == [1]
    assert service._modification_names == {"m6A": 1}


def test_validate_entry(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()

    service = DataService(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        modification_ids=1,
        technology_id=1,
        organism_id=1,
    )
    assert service._validate_entry() is None


def test_validate_existing_entry(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        # force/add dataset manually
        stamp = datetime.now(timezone.utc).replace(microsecond=0)
        dataset = Dataset(
            id="123456789ABC",
            project_id=smid,
            organism_id=1,
            technology_id=1,
            title="title",
            modification_type="RNA",
            date_added=stamp,
        )
        association = DatasetModificationAssociation(
            dataset_id="123456789ABC", modification_id=1
        )
        session.add_all([dataset, association])
        session.commit()

    service = DataService(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        modification_ids=1,
        technology_id=1,
        organism_id=1,
    )
    with pytest.raises(DatasetExistsError) as exc:
        service._validate_entry()
    assert str(exc.value) == (
        "Suspected duplicate record with EUFID = 123456789ABC "
        f"(SMID = {smid}), and title = title. Aborting transaction!"
    )
    assert exc.type == DatasetExistsError


def test_add_association(Session, setup, project_template):
    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)

    service = DataService(
        session=Session(),
        smid=smid,
        title="title",
        filen="filen",
        assembly_id=1,
        modification_ids=[1, 2],
        technology_id=1,
        organism_id=1,
    )
    service._create_eufid()
    service._add_association()
    assert service._selection_ids == [1, 4]
    assert service._modification_names == {"m6A": 1, "m5C": 2}
    assert service.get_eufid() == service._eufid
