import pytest

from scimodom.api.project import project_api
from scimodom.services.project import ProjectService
from scimodom.services.url import PROJECT_API_ROUTE
from scimodom.services.user import UserService
from scimodom.utils.dtos.project import (
    ProjectTemplate,
    ProjectSourceDto,
    ProjectMetaDataDto,
    ProjectOrganismDto,
)
from tests.api.schematise import validate, client_fixture

# Swagger docs/OpenAPI definitions for project API
# are split into project (request) and browse
PROJECT_SCHEMA = "project.yaml"
BROWSE_SCHEMA = "browse.yaml"

client = client_fixture(project_api, PROJECT_API_ROUTE)
auth_client = client_fixture(project_api, PROJECT_API_ROUTE, authenticated=True)

PROJECT_REQUEST = ProjectTemplate(
    title="My project",
    summary="A summary",
    contact_name="Ada Lovelace",
    contact_institution="Analytical Engines",
    contact_email="ada@example.org",
    external_sources=[ProjectSourceDto(doi="10.1234/x", pmid=12345)],
    metadata=[
        ProjectMetaDataDto(
            rna="WTS",
            modomics_id="2000000006A",
            tech="Tech-seq",
            method_id="0ee048bc",
            organism=ProjectOrganismDto(
                taxa_id=9606, cto="Cell", assembly_name="GRCh38"
            ),
        )
    ],
)


@pytest.fixture
def services(Session, project, mocker):
    mock_file_service = mocker.MagicMock()
    mock_file_service.create_project_request_file.return_value.__enter__.return_value = (
        mocker.MagicMock()
    )
    project_service = ProjectService(
        session=Session(),
        file_service=mock_file_service,
        selection_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.project.get_project_service",
        return_value=project_service,
    )
    user_service = UserService(
        session=Session(),
        mail_service=mocker.Mock(),
    )
    mocker.patch(
        "scimodom.api.project.get_user_service",
        return_value=user_service,
    )
    mocker.patch(
        "scimodom.api.project.get_mail_service",
        return_value=mocker.Mock(),
    )


def prefix_url(path: str) -> str:
    return f"{PROJECT_API_ROUTE}{path}"


def test_projects_schema(client, services):
    response = client.get(prefix_url("/projects"))
    assert response.json
    validate(BROWSE_SCHEMA, response, 200)


def test_my_projects_schema(auth_client, services):
    response = auth_client.get(prefix_url("/users/me/projects"))
    assert response.json
    validate(BROWSE_SCHEMA, response, 200)


def test_project_request_schema(auth_client, services):
    response = auth_client.post(
        prefix_url("/projects/requests"), json=PROJECT_REQUEST.model_dump()
    )
    validate(PROJECT_SCHEMA, response, 201)
