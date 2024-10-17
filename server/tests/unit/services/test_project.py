from datetime import datetime
from pathlib import Path
from typing import TextIO

import pytest
from sqlalchemy import func, select

from tests.mocks.io_mocks import MockStringIO, MockBytesIO
from scimodom.database.models import (
    Modification,
    DetectionTechnology,
    Project,
    ProjectSource,
    ProjectContact,
    Selection,
    User,
    UserProjectAssociation,
)
from scimodom.services.project import ProjectService, DuplicateProjectError
from scimodom.utils.dtos.project import (
    ProjectTemplate,
    ProjectMetaDataDto,
    ProjectOrganismDto,
    ProjectSourceDto,
)
from scimodom.utils.specs.enums import UserState


class MockFileService:
    def __init__(self):
        self.files_by_name: dict[str, MockStringIO | MockBytesIO] = {}
        self.deleted_requests: list[str] = []
        self.deleted_projects: list[str] = []

    def create_project_metadata_file(self, smid: str) -> TextIO:
        metadata_file = Path(
            self._get_project_metadata_dir(), f"{smid}.json"
        ).as_posix()
        new_file = MockStringIO()
        self.files_by_name[metadata_file] = new_file
        return new_file

    def create_project_request_file(self, request_uuid) -> TextIO:
        request_file = Path(
            self._get_project_request_file_path(request_uuid)
        ).as_posix()
        new_file = MockStringIO()
        self.files_by_name[request_file] = new_file
        return new_file

    def delete_project_request_file(self, request_uuid) -> None:
        name = self._get_project_request_file_path(request_uuid).as_posix()
        self.deleted_requests.append(name)

    def delete_project_metadata_file(self, smid) -> None:
        name = Path(self._get_project_metadata_dir(), f"{smid}.json").as_posix()
        self.deleted_projects.append(name)

    def _get_project_metadata_dir(self) -> Path:
        return Path("/data", "metadata")

    def _get_project_request_file_path(self, request_uuid):
        return Path(self._get_project_request_dir(), f"{request_uuid}.json")

    def _get_project_request_dir(self):
        return Path(self._get_project_metadata_dir(), "project_requests")


@pytest.fixture
def file_service():
    yield MockFileService()


def _get_project_service(Session, file_service):
    return ProjectService(Session(), file_service=file_service)  # noqa


PROJECT = ProjectTemplate(
    title="Title",
    summary="Summary",
    contact_name="Contact Name",
    contact_institution="Contact Institution",
    contact_email="email@example.com",
    date_published="2024-01-01",
    external_sources=[ProjectSourceDto(doi="DOI", pmid=12345678)],
    metadata=[
        ProjectMetaDataDto(
            rna="WTS",
            modomics_id="2000000006A",
            tech="Tech-seq",
            method_id="0ee048bc",
            organism=ProjectOrganismDto(
                taxa_id=9606, cto="Cell", assembly_name="GRCh38"
            ),
        ),
        ProjectMetaDataDto(
            rna="WTS",
            modomics_id="2000000005C",
            tech="Tech-seq",
            method_id="0ee048bc",
            organism=ProjectOrganismDto(
                taxa_id=10090, cto="Organ", assembly_name="GRCm38"
            ),
        ),
    ],
)


EXPECTED_PROJECT_TEMPLATE = """{
    "title": "Title",
    "summary": "Summary",
    "contact_name": "Contact Name",
    "contact_institution": "Contact Institution",
    "contact_email": "email@example.com",
    "date_published": "2024-01-01T00:00:00",
    "external_sources": [
        {
            "doi": "DOI",
            "pmid": 12345678
        }
    ],
    "metadata": [
        {
            "rna": "WTS",
            "modomics_id": "2000000006A",
            "tech": "Tech-seq",
            "method_id": "0ee048bc",
            "organism": {
                "taxa_id": 9606,
                "cto": "Cell",
                "assembly_name": "GRCh38",
                "assembly_id": null
            },
            "note": null
        },
        {
            "rna": "WTS",
            "modomics_id": "2000000005C",
            "tech": "Tech-seq",
            "method_id": "0ee048bc",
            "organism": {
                "taxa_id": 10090,
                "cto": "Organ",
                "assembly_name": "GRCm38",
                "assembly_id": null
            },
            "note": null
        }
    ]
}"""


# tests


def test_create_project_request(Session, file_service):
    service = _get_project_service(Session, file_service)
    uuid = service.create_project_request(PROJECT)
    assert (
        file_service.files_by_name[
            f"/data/metadata/project_requests/{uuid}.json"
        ].final_content
        == EXPECTED_PROJECT_TEMPLATE
    )


def test_project_validate_entry(Session, file_service):
    service = _get_project_service(Session, file_service)
    assert service._validate_entry(PROJECT) is None


def test_project_validate_existing_entry(Session, file_service, setup):
    smid = "12345678"
    with Session() as session, session.begin():
        session.add_all(setup)
        contact = ProjectContact(
            contact_name="Contact Name",
            contact_institution="Contact Institution",
            contact_email="email@example.com",
        )
        session.add(contact)
        session.flush()
        project = Project(
            id=smid,
            title="Title",
            summary="Summary",
            contact_id=contact.id,
            date_published=datetime.fromisoformat("2024-01-01"),
            date_added=datetime.now(),
        )
        source = ProjectSource(project_id=smid, doi="DOI", pmid=12345678)
        session.add_all([project, source])
        session.commit()

    service = _get_project_service(Session, file_service)
    with pytest.raises(DuplicateProjectError) as exc:
        service._validate_entry(PROJECT)
    assert (
        str(exc.value)
        == "Suspected duplicate project with SMID '12345678' and title 'Title'."
    )


def test_project_add_selection(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)

        service = _get_project_service(Session, file_service)
        service._add_selection_if_none(PROJECT)

    expected_records = [(1, 1, 1, 1), (2, 2, 2, 1)]
    with Session() as session, session.begin():
        records = session.execute(select(Selection)).scalars().all()
        records = [
            (r.id, r.modification_id, r.organism_id, r.technology_id) for r in records
        ]
        assert records == expected_records


def test_project_add_selection_exists(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
        technology = DetectionTechnology(method_id="0ee048bc", tech="Tech-seq")
        session.add(technology)
        session.flush()
        selection = Selection(
            modification_id=1, organism_id=3, technology_id=technology.id
        )
        session.add(selection)
        session.flush()

        service = _get_project_service(Session, file_service)
        service._add_selection_if_none(PROJECT)

    expected_records = [(1, 1, 3, 1), (2, 1, 1, 1), (3, 2, 2, 1)]
    with Session() as session, session.begin():
        records = session.execute(select(Selection)).scalars().all()
        records = [
            (r.id, r.modification_id, r.organism_id, r.technology_id) for r in records
        ]
        assert records == expected_records


def test_project_add_modification(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
        modification = Modification(modomics_id="2000000006A", rna="WTS")
        session.add(modification)
        session.commit()

    service = _get_project_service(Session, file_service)
    for metadata, expected_modification_id in zip(PROJECT.metadata, [1, 2]):
        assert service._add_modification_if_none(metadata) == expected_modification_id


def test_project_add_technology(Session, file_service, setup):
    service = _get_project_service(Session, file_service)
    for metadata in PROJECT.metadata:
        assert service._add_technology_if_none(metadata) == 1


def test_project_add_organism(Session, file_service, setup):
    service = _get_project_service(Session, file_service)
    for metadata, expected_organism_id in zip(PROJECT.metadata, [1, 2]):
        assert service._add_organism_if_none(metadata) == expected_organism_id


def test_project_add_contact(Session, file_service):
    with Session() as session, session.begin():
        contact = ProjectContact(
            contact_name="Another contact Name",
            contact_institution="Contact Institution",
            contact_email="another_email@example.com",
        )
        session.add(contact)
        session.commit()

    service = _get_project_service(Session, file_service)
    assert service._add_contact_if_none(PROJECT) == 2


def test_project_add_project(Session, file_service, setup, freezer):
    with Session() as session, session.begin():
        session.add_all(setup)

        freezer.move_to("2024-06-20 12:00:00")
        service = _get_project_service(Session, file_service)
        smid = service._add_project(PROJECT)

    with Session() as session, session.begin():
        project = session.get_one(Project, smid)
        assert project.title == "Title"
        assert project.summary == "Summary"
        assert project.date_published == datetime(2024, 1, 1)
        assert project.date_added == datetime(2024, 6, 20, 12, 0, 0)
        contact = session.get_one(ProjectContact, project.contact_id)
        assert contact.contact_name == "Contact Name"
        assert contact.contact_institution == "Contact Institution"
        assert contact.contact_email == "email@example.com"
        source = session.execute(select(ProjectSource)).scalars().all()
        assert len(source) == 1
        assert source[0].project_id == smid
        assert source[0].doi == "DOI"
        assert source[0].pmid == 12345678


def test_create_project(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = _get_project_service(Session, file_service)
    smid = service.create_project(PROJECT, "abcdef123456")
    assert (
        file_service.files_by_name[f"/data/metadata/{smid}.json"].final_content
        == EXPECTED_PROJECT_TEMPLATE
    )
    assert file_service.deleted_requests == [
        "/data/metadata/project_requests/abcdef123456.json"
    ]


def test_project_get_by_id(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = _get_project_service(Session, file_service)
    smid = service._add_project(PROJECT)
    project = service.get_by_id(smid)
    assert project.id == smid
    assert project.title == "Title"
    assert project.summary == "Summary"


def test_query_projects(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
        for name, email, smid, title, summary in zip(
            ["Name 1", "Name 2"],
            ["email1@example.com", "email2@example.com"],
            ["12345678", "12345679"],
            ["Title 1", "Title 2"],
            ["Summary 1", "Summary 2"],
        ):
            contact = ProjectContact(
                contact_name=name,
                contact_institution="Contact Institution",
                contact_email=email,
            )
            session.add(contact)
            session.flush()
            project = Project(
                id=smid,
                title=title,
                summary=summary,
                contact_id=contact.id,
                date_added=datetime(2024, 6, 20, 12, 0, 0),
            )
            session.add(project)
        user = User(
            email="email1@example.com", state=UserState.active, password_hash="xxx"
        )
        session.add(user)
        session.flush()
        user_permission = UserProjectAssociation(user_id=user.id, project_id="12345678")
        session.add(user_permission)
        session.commit()

    service = _get_project_service(Session, file_service)
    with Session() as session, session.begin():
        user = session.get_one(User, 1)
        assert len(service.get_projects(user=user)) == 1
        assert len(service.get_projects()) == 2


def test_delete_project(Session, project, file_service):
    service = _get_project_service(Session, file_service)
    service.delete_project(project[0])
    service.delete_project(project[1])

    with Session() as session:
        assert session.scalar(select(func.count()).select_from(Project)) == 0
        assert session.scalar(select(func.count()).select_from(ProjectSource)) == 0
        assert session.scalar(select(func.count()).select_from(ProjectContact)) == 0
        assert (
            session.scalar(select(func.count()).select_from(UserProjectAssociation))
            == 0
        )
    assert file_service.deleted_projects == [
        "/data/metadata/12345678.json",
        "/data/metadata/ABCDEFGH.json",
    ]
