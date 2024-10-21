from typing import Generator

import pytest

from scimodom.services.sunburst import SunburstService
from scimodom.utils.specs.enums import SunburstChartType


EXTECTED_SEARCH_CACHE_CONTENT = """[{"name": "Search", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}, {"name": "Technology 2", "size": 4}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""

# returns 5 datasets while there are actually 4, dataset 1 having both m5C and m6A
EXTECTED_BROWSE_CACHE_CONTENT = """[{"name": "Browse", "children": [{"name": "m5C", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}, {"name": "m6A", "children": [{"name": "H. sapiens", "children": [{"name": "Cell type 1", "children": [{"name": "Technology 1", "size": 1}, {"name": "Technology 2", "size": 1}]}, {"name": "Cell type 2", "children": [{"name": "Technology 2", "size": 1}]}]}]}]}]"""


class MockFileService:
    def __init__(self):
        self._sunburst_cache_content = ""

    def update_sunburst_cache(
        self, name: str, generator: Generator[str, None, None]
    ):  # noqa
        for element in generator:
            self._sunburst_cache_content += element


@pytest.fixture
def sunburst_service(Session):
    yield SunburstService(session=Session(), file_service=MockFileService())


def test_update_search_cache(sunburst_service: SunburstService, dataset):
    sunburst_service.update_cache(SunburstChartType.search)
    assert (
        sunburst_service._file_service._sunburst_cache_content
        == EXTECTED_SEARCH_CACHE_CONTENT
    )


def test_update_browse_cache(sunburst_service: SunburstService, dataset):
    sunburst_service.update_cache(SunburstChartType.browse)
    assert (
        sunburst_service._file_service._sunburst_cache_content
        == EXTECTED_BROWSE_CACHE_CONTENT
    )
