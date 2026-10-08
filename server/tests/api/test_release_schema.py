from scimodom.api.release import release_api
from scimodom.services.url import RELEASE_API_ROUTE
from scimodom.services.utilities import UtilitiesService
from tests.api.schematise import validate, client_fixture

SCHEMA = "release.yaml"

client = client_fixture(release_api, RELEASE_API_ROUTE)


def prefix_url(path: str) -> str:
    return f"{RELEASE_API_ROUTE}{path}"


def test_info_schema(client, Session, mocker):
    utilities_service = UtilitiesService(Session())
    mocker.patch(
        "scimodom.api.release.get_utilities_service",
        return_value=utilities_service,
    )
    response = client.get(f"{RELEASE_API_ROUTE}/info")
    validate(SCHEMA, response, 200)
