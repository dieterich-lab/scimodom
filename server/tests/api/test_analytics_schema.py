from io import BytesIO

import pytest

from scimodom.api.analytics import analytics_api
from scimodom.services.file import CacheNotAvailableException
from scimodom.services.url import ANALYTICS_API_ROUTE
from scimodom.utils.specs.enums import IndexCacheType
from tests.api.schematise import validate, client_fixture

SCHEMA = "analytics.yaml"
client = client_fixture(analytics_api, ANALYTICS_API_ROUTE)

SUNBURST = b'[{"name": "root", "children": [{"name": "m6A", "size": 3}]}]'


class MockSunburstService:
    @staticmethod
    def open_json(sunburst_type):
        return BytesIO(SUNBURST)


class MockMissingSunburstService:
    @staticmethod
    def open_json(sunburst_type):
        raise CacheNotAvailableException(IndexCacheType.SUNBURST)


def prefix_url(path: str) -> str:
    return f"{ANALYTICS_API_ROUTE}/charts/sunbursts?view={path}"


@pytest.mark.parametrize("sunburst_type", ["search", "browse"])
def test_sunbursts_schema(client, mocker, sunburst_type):
    mocker.patch(
        "scimodom.api.analytics.get_sunburst_service",
        return_value=MockSunburstService(),
    )
    response = client.get(prefix_url(f"{sunburst_type}"))
    validate(SCHEMA, response, 200)


@pytest.mark.parametrize("sunburst_type", ["search", "browse"])
def test_sunbursts_not_available_schema(client, mocker, sunburst_type):
    mocker.patch(
        "scimodom.api.analytics.get_sunburst_service",
        return_value=MockMissingSunburstService(),
    )
    mocker.patch(
        "scimodom.api.helpers.errors.get_external_service",
        return_value=mocker.Mock(),
    )
    response = client.get(prefix_url(f"{sunburst_type}"))
    validate(SCHEMA, response, 503)
    assert response.headers["Retry-After"]
