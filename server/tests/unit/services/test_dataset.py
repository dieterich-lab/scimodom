import pytest

# NOTE: ultimately relies on ProjectService(Session(), project).create_project()
# to avoid using ProjectService, we force/add project directly - skip checks


def _get_file():
    from io import StringIO

    string = """#fileformat=bedRModv1.6
    #organism=9606
    #modification_type=RNA
    #assembly=GRCh38
    #annotation_source=Annotation
    #annotation_version=
    #sequencing_platform=Sequencing platform
    #basecalling=
    #bioinformatics_workflow=Workflow
    #experiment=Description of experiment.
    #external_source=
    #chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency\trefBase
    1\t139219\t139220\tm6A\t100\t+\t139219\t139220\t0,0,0\t50\t10\tA
    1\t139220\t139221\tm5C\t5\t+\t139220\t139221\t0,0,0\t100\t5\tA
    1\t139221\t139222\tm5C\t5\t+\t139221\t139222\t0,0,0\t300\t5\tA
    1\t139222\t139223\tm6A\t500\t+\t139222\t139223\t0,0,0\t250\t100\tA
    1\t139223\t139224\tm6A\t5\t+\t139223\t139224\t0,0,0\t10\t5\tA"""
    return StringIO(string)


def _get_project(project_template, case=None):
    # set selection 2 to m5C, but same cell type as 1
    project = project_template.copy()
    if case == "two":
        project["metadata"][1]["modomics_id"] = "5C"
        project["metadata"][1]["organism"]["cto"] = "Cell Type 1"
    return project


def _add_selection(session, metadata):
    import scimodom.utils.utils as utils
    import scimodom.database.queries as queries
    from scimodom.database.models import (
        Modification,
        DetectionTechnology,
        Organism,
        Selection,
    )

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
        selection_id = selection.id


def _add_contact(session, project):
    from scimodom.database.models import ProjectContact

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
    from datetime import datetime, timezone
    import scimodom.utils.utils as utils
    from scimodom.services.project import ProjectService
    from scimodom.database.models import Project, ProjectSource

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


@pytest.mark.parametrize(
    "selection",
    [
        ("one"),
        ("two"),
        ("none"),
    ],
)
def test_dataset_get_selection(selection, Session, setup, project_template):
    from io import StringIO
    from scimodom.services.dataset import DataService

    project = _get_project(project_template, case=selection)

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project)
        session.commit()

    modification_ids = [1, 2]
    if selection == "one":
        _ = modification_ids.pop(1)
    taxa_id = 9606
    assembly_id = 1
    technology_id = 1
    organism_id = 1

    service = DataService(
        Session(),
        smid,
        "Dataset title",
        "filename",
        StringIO("filename"),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    # for some cases we have "sqlalchemy.exc.NoResultFound: No row was found when one was required"
    # that "bypasses" the except?
    if selection == "none":
        with pytest.raises(Exception) as excinfo:
            service._get_selection()
    else:
        service._get_selection()


def test_dataset_validate_entry(Session, setup, project_template):
    from io import StringIO
    from scimodom.services.dataset import DataService

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()

    taxa_id = 9606
    assembly_id = 1
    modification_ids = [1]
    technology_id = 1
    organism_id = 1

    service = DataService(
        Session(),
        smid,
        "Dataset title",
        "filename",
        StringIO("filename"),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    assert service._validate_entry() is None


def test_dataset_validate_existing_entry(Session, setup, project_template):
    from io import StringIO
    from scimodom.services.dataset import DataService, DuplicateDatasetError
    from scimodom.database.models import Dataset, Association

    taxa_id = 9606
    assembly_id = 1
    modification_ids = [1]
    technology_id = 1
    organism_id = 1
    title = "Dataset title"

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        # force/add dataset manually
        dataset = Dataset(
            id="123456789ABC",
            project_id=smid,
            title=title,
            file_format="bedRModv1.6",
            modification_type="RNA",
            taxa_id=taxa_id,
            assembly_id=assembly_id,
            lifted=False,
            annotation_source="source",
            annotation_version="version",
        )
        association = Association(dataset_id="123456789ABC", selection_id=1)
        session.add_all([dataset, association])
        session.commit()

    service = DataService(
        Session(),
        smid,
        title,
        "filename",
        StringIO("filename"),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    service._get_selection()
    with pytest.raises(DuplicateDatasetError) as excinfo:
        service._validate_entry()


def test_dataset_validate_assembly(Session, setup, project_template):
    from io import StringIO
    from scimodom.services.dataset import DataService
    from scimodom.database.models import Assembly
    import scimodom.database.queries as queries

    taxa_id = 9606
    modification_ids = [1]
    technology_id = 1
    organism_id = 1

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        assembly = Assembly(name="GRCh19", taxa_id=taxa_id, version="123456789ABC")
        session.add(assembly)
        session.flush()
        query = queries.query_column_where("Assembly", "id", filters={"name": "GRCh19"})
        assembly_id = session.execute(query).scalar()
        session.commit()

    service = DataService(
        Session(),
        smid,
        "Dataset title",
        "filename",
        StringIO("filename"),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    service._validate_assembly()
    assert service._lifted is True


@pytest.mark.parametrize(
    "selection",
    [
        ("one"),
        ("two"),
    ],
)
def test_dataset_create_eufid(selection, Session, setup, project_template):
    from scimodom.services.dataset import DataService

    # two modifications for the same dataset, same technology, same organism
    project = _get_project(project_template, case=selection)

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project)
        session.commit()

    taxa_id = 9606
    assembly_id = 1
    modification_ids = [1, 2]
    if selection == "one":
        _ = modification_ids.pop(1)
    technology_id = 1
    organism_id = 1

    service = DataService(
        Session(),
        smid,
        "Dataset title",
        "filename",
        _get_file(),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    service._get_selection()
    if selection == "one":
        with pytest.raises(Exception) as excinfo:
            service._create_eufid()
    else:
        service._create_eufid()


def test_dataset_add_association(Session, setup, project_template):
    from sqlalchemy import select
    from io import StringIO
    from scimodom.services.dataset import DataService
    from scimodom.database.models import Association, Selection

    with Session() as session, session.begin():
        session.add_all(setup)
        smid = _mock_project_service(session, project_template)
        session.commit()

    taxa_id = 9606
    assembly_id = 1
    modification_ids = [1]
    technology_id = 1
    organism_id = 1

    service = DataService(
        Session(),
        smid,
        "Dataset title",
        "filename",
        StringIO("filename"),
        taxa_id,
        assembly_id,
        modification_ids,
        technology_id,
        organism_id,
    )
    service._get_selection()
    service._eufid = "123456789ABC"
    service._add_association()

    with Session() as session, session.begin():
        records = session.execute(select(Association)).scalar()
        assert records.id == 1
        assert records.dataset_id == "123456789ABC"
        assert records.selection_id == 1
        records = session.execute(select(Selection)).scalar()
        assert records.id == 1
        assert records.modification_id == modification_ids[0]
        assert records.technology_id == technology_id
        assert records.organism_id == organism_id
