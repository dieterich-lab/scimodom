from io import StringIO
from typing import Any, Iterable, Sequence

import pytest
from flask import Flask

from scimodom.api.modification import (
    modification_api,
    IntersectResponse,
)
from scimodom.utils.dtos.bedtools import Bed6Record
from scimodom.utils.specs.enums import Strand, TargetsFileType


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(modification_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def mock_services(mocker):
    mocker.patch(
        "scimodom.api.modification.get_file_service", return_value=MockFileService()
    )
    mocker.patch(
        "scimodom.api.modification.get_bedtools_service",
        return_value=MockBedtoolsService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_assembly_service", return_value=MockAssemblyService()
    )


class MockAssemblyService:
    VALID_TAXA = [9606, 10090, 7227]

    @staticmethod
    def get_chroms(taxa_id: int) -> list[dict[str, Any]]:
        if taxa_id in MockAssemblyService.VALID_TAXA:
            return [{"chrom": "1", "size": 248956422}]
        else:
            raise FileNotFoundError


class MockUtilitiesService:
    @staticmethod
    def get_taxa() -> list[dict[str, Any]]:
        return [
            {
                "id": 9606,
                "taxa_sname": "H. sapiens",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Chordata",
            },
            {
                "id": 10090,
                "taxa_sname": "M. musculus",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Chordata",
            },
            {
                "id": 7227,
                "taxa_sname": "D. melanogaster",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Arthropoda",
            },
        ]


class MockFileService:
    VALID_TAXA = [9606, 10090]
    FILE_CONTENT = {
        TargetsFileType.MIRNA: "1\t3284722\t3284729\tTargetScan:Target:miR\t75\t+",
        TargetsFileType.RBP: "1\t2403126\t2403133\toRNAment:Target:1:Motif\t750\t+",
    }

    @staticmethod
    def open_file_for_reading(path):  # noqa
        return StringIO("")

    @staticmethod
    def open_annotation_targets_file(
        taxa_id: int, target_type: TargetsFileType, chrom: str
    ):  # noqa
        if taxa_id in MockFileService.VALID_TAXA and isinstance(
            target_type, TargetsFileType
        ):
            return StringIO(MockFileService.FILE_CONTENT[target_type])
        else:
            raise FileNotFoundError


class MockBedtoolsService:
    RECORDS = [
        Bed6Record(
            chrom="1",
            start=3284722,
            end=3284729,
            name="TargetScan:Target:miR",
            score=75,
            strand=Strand.FORWARD,
        ),
        Bed6Record(
            chrom="1",
            start=2403126,
            end=2403133,
            name="oRNAment:Target:1:Motif",
            score=750,
            strand=Strand.FORWARD,
        ),
    ]

    @staticmethod
    def create_temp_file_from_records(
        records: Iterable[Sequence[Any]], sort: bool = True
    ) -> str:  # noqa
        MockBedtoolsService.INTERSECTION_RECORDS = []
        return "/tmp/pybedtools.tmp"

    @staticmethod
    def intersect_bed6_records(
        a_records: Iterable[Bed6Record],
        b_stream: StringIO,
        is_strand: bool,
        is_sorted: bool = True,
    ) -> Iterable[Bed6Record]:  # noqa
        line = b_stream.getvalue()
        if "TargetScan" in line:
            MockBedtoolsService.INTERSECTION_RECORDS = [MockBedtoolsService.RECORDS[0]]
        else:
            MockBedtoolsService.INTERSECTION_RECORDS = [MockBedtoolsService.RECORDS[1]]
        return MockBedtoolsService.INTERSECTION_RECORDS


@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "/target/MIRNAs?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=%2B",
            404,
            "Unknown targets type",
        ),
        (
            "/target/MIRNA?taxaId=9605&chrom=1&start=3284723&end=3284724&strand=%2B",
            404,
            "Unrecognized Taxa ID",
        ),
        (
            "/target/MIRNA?taxaId=a&chrom=1&start=3284723&end=3284724&strand=%2B",
            400,
            "Invalid Taxa ID",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=I&start=3284723&end=3284724&strand=%2B",
            404,
            "Unrecognized chrom 'I' for Taxa '9606'",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284722&strand=%2B",
            400,
            "Invalid coordinates: start must be smaller than end",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=248956422&strand=%2B",
            400,
            "Invalid coordinates: end is greater than chrom size",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=+",
            400,
            "Invalid strand value",
        ),
    ],
)
def test_get_modification_targets_bad_url(
    test_client, mock_services, url, http_status, message
):
    result = test_client.get(url)
    assert result.status_code == http_status
    assert result.json["message"] == message


@pytest.mark.parametrize(
    "url",
    [
        "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=%2B",
        "/target/RBP?taxaId=9606&chrom=1&start=2403131&end=2403132&strand=%2B",
    ],
)
def test_get_modification_targets(test_client, mock_services, url):
    result = test_client.get(url)
    assert result.status == "200 OK"
    assert (
        IntersectResponse.model_validate_json(result.text).records
        == MockBedtoolsService.INTERSECTION_RECORDS
    )


def test_get_modification_targets_empty(test_client, mock_services, caplog):
    url = "/target/MIRNA?taxaId=7227&chrom=1&start=3284723&end=3284724&strand=%2B"
    result = test_client.get(url)
    assert result.status == "200 OK"
    assert (
        IntersectResponse.model_validate_json(result.text).records
        == MockBedtoolsService.INTERSECTION_RECORDS
    )
    assert caplog.record_tuples == [
        (
            "scimodom.api.modification",
            30,
            "API not implemented for Taxa ID '7227': silently returning empty response!",
        )
    ]
