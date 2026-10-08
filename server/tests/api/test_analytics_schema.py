from contextlib import contextmanager
from io import BytesIO

import pytest

from scimodom.api.analytics import analytics_api
from scimodom.services.url import ANALYTICS_API_ROUTE
from tests.api.schematise import validate, client_fixture

SCHEMA = "analytics.yaml"
client = client_fixture(analytics_api, ANALYTICS_API_ROUTE)

SUNBURST = b'[{"name": "root", "children": [{"name": "m6A", "size": 3}]}]'


class MockSunburstService:
    @staticmethod
    @contextmanager
    def open_json(sunburst_type):
        yield BytesIO(SUNBURST)


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
