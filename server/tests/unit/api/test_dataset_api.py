from io import StringIO
from typing import Iterable

import pytest
from flask import Flask

from scimodom.api.dataset import (
    dataset_api,
    IntersectResponse,
    ClosestResponse,
    SubtractResponse,
)
from scimodom.database.models import Data
from scimodom.utils.bedtools_dto import (
    ComparisonRecord,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
    EufRecord,
    Bed6Record,
)
from scimodom.utils.common_dto import Strand


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(dataset_api, url_prefix="")
    yield app.test_client()


class MockFileService:
    VALID_TEMP_FILE_ID = "im_the_only_valid_temp_file_id"
    FILE_CONTENT = "temp file content"

    @staticmethod
    def check_tmp_upload_file_id(file_id):
        return file_id == MockFileService.VALID_TEMP_FILE_ID

    @staticmethod
    def open_tmp_upload_file_by_id(file_id):
        if file_id == MockFileService.VALID_TEMP_FILE_ID:
            return StringIO(MockFileService.FILE_CONTENT)
        else:
            raise FileNotFoundError("That is no valid file ID")


def _get_dummy_data_record(dataset_id, data_id):
    return Data(
        id=data_id,
        dataset_id=dataset_id,
        modification_id=10,
        chrom="17",
        start=100001,
        end=120000,
        name="Y",
        score=1000,
        strand=Strand.FORWARD,
        thick_start=100101,
        thick_end=100201,
        item_rgb="128,128,0",
        coverage=43,
        frequency=100,
    )


DATA_BY_DATASET_ID = {
    "datasetidAxx": [_get_dummy_data_record("datasetidAxx", i) for i in range(3)],
    "datasetidBxx": [_get_dummy_data_record("datasetidBxx", i) for i in range(2)],
    "datasetidCxx": [_get_dummy_data_record("datasetidCxx", i) for i in range(1)],
}


class MockDataService:
    @staticmethod
    def get_by_dataset(dataset_id):
        for r in DATA_BY_DATASET_ID[dataset_id]:
            yield r


class MockBedtoolsService:
    last_operation = "none"
    last_a_dataset = []
    last_b_dataset_list = []
    last_is_strand = False

    DEFAULT_COMPARISON_RECORD = ComparisonRecord(
        chrom="X",
        start=1,
        end=2,
        name="Hugo",
        score=3,
        strand=Strand.FORWARD,
        coverage=4,
        frequency=5,
        eufid="some_euf_id_",
    )

    INTERSECT_RESULT = [
        IntersectRecord(
            a=DEFAULT_COMPARISON_RECORD,
            b=DEFAULT_COMPARISON_RECORD,
        )
    ]
    CLOSEST_RESULT = [
        ClosestRecord(
            a=DEFAULT_COMPARISON_RECORD, b=DEFAULT_COMPARISON_RECORD, distance=50
        )
    ]
    SUBTRACT_RESULT = [SubtractRecord(**DEFAULT_COMPARISON_RECORD.dict())]

    def intersect(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
    ) -> Iterable[IntersectRecord]:
        self._log_operation("intersect", a_records, b_records_list, is_strand)
        return MockBedtoolsService.INTERSECT_RESULT

    @staticmethod
    def _log_operation(operation, a_records, b_records_list, is_strand):
        MockBedtoolsService.last_operation = operation
        MockBedtoolsService.last_a_dataset = list(a_records)
        MockBedtoolsService.last_b_dataset_list = [list(x) for x in b_records_list]
        MockBedtoolsService.last_is_strand = is_strand

    def closest(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
    ) -> Iterable[ClosestRecord]:
        self._log_operation("closest", a_records, b_records_list, is_strand)
        return MockBedtoolsService.CLOSEST_RESULT

    def subtract(
        self,
        a_records: Iterable[ComparisonRecord],
        b_records_list: list[Iterable[ComparisonRecord]],
        is_strand: bool,
    ) -> Iterable[SubtractRecord]:
        self._log_operation("subtract", a_records, b_records_list, is_strand)
        return MockBedtoolsService.SUBTRACT_RESULT


class MockBed6Importer:
    RESULT = [
        Bed6Record(
            chrom="bed6", start=1, end=2, name="abc", score=10, strand=Strand.FORWARD
        )
    ]

    RESULT_AS_COMPARISON = [
        ComparisonRecord(**x.__dict__, coverage=0, frequency=1, eufid="upload      ")
        for x in RESULT
    ]

    def __init__(self, stream):
        assert stream.read() == MockFileService.FILE_CONTENT

    @staticmethod
    def parse():
        for x in MockBed6Importer.RESULT:
            yield x


class MockEufImporter:
    RESULT = [
        EufRecord(
            chrom="EUF",
            start=102,
            end=303,
            name="abc",
            score=11,
            strand=Strand.REVERSE,
            thick_start=150,
            thick_end=250,
            item_rgb="0,0,0",
            coverage=50,
            frequency=80,
        )
    ]

    RESULT_AS_COMPARISON = [
        ComparisonRecord(**x.__dict__, eufid="upload      ") for x in RESULT
    ]

    def __init__(self, stream):
        assert stream.read() == MockFileService.FILE_CONTENT

    @staticmethod
    def parse():
        for x in MockEufImporter.RESULT:
            yield x


@pytest.fixture
def comparison_services(mocker):
    mocker.patch(
        "scimodom.api.dataset.get_file_service", return_value=MockFileService()
    )
    mocker.patch(
        "scimodom.api.helpers.get_file_service", return_value=MockFileService()
    )
    mocker.patch(
        "scimodom.api.dataset.get_data_service", return_value=MockDataService()
    )
    mocker.patch(
        "scimodom.api.dataset.get_bedtools_service", return_value=MockBedtoolsService()
    )
    mocker.patch("scimodom.api.dataset.Bed6Importer", return_value=MockBed6Importer)
    mocker.patch("scimodom.api.dataset.EufImporter", return_value=MockEufImporter)


@pytest.mark.parametrize(
    "reference,comparison,upload,euf,strand",
    [
        (["datasetidAxx"], ["datasetidBxx"], None, None, True),
        (["datasetidAxx", "datasetidBxx"], ["datasetidCxx"], None, None, True),
        (["datasetidAxx"], ["datasetidBxx", "datasetidCxx"], None, None, False),
        (["datasetidAxx"], None, MockFileService.VALID_TEMP_FILE_ID, False, False),
        (["datasetidBxx"], None, MockFileService.VALID_TEMP_FILE_ID, True, False),
    ],
)
def test_intersect(
    test_client, comparison_services, reference, comparison, upload, euf, strand
):
    result = test_client.get(
        get_compare_url_parameters(
            "intersect", reference, comparison, upload, euf, strand
        )
    )
    assert result.status == "200 OK"
    assert (
        IntersectResponse.model_validate_json(result.text).records
        == MockBedtoolsService.INTERSECT_RESULT
    )
    check_comparison_mocks("intersect", reference, comparison, upload, euf, strand)


def check_comparison_mocks(operation, reference, comparison, upload, euf, strand):
    assert MockBedtoolsService.last_operation == operation
    assert MockBedtoolsService.last_is_strand == strand
    assert MockBedtoolsService.last_a_dataset == get_a_datasets_as_comparison_records(
        *reference
    )
    if comparison is not None:
        assert (
            MockBedtoolsService.last_b_dataset_list
            == get_b_dataset_list_as_comparison_records(*comparison)
        )
    if upload is not None:
        if euf:
            assert MockBedtoolsService.last_b_dataset_list == [
                MockEufImporter.RESULT_AS_COMPARISON
            ]
        else:
            assert MockBedtoolsService.last_b_dataset_list == [
                MockBed6Importer.RESULT_AS_COMPARISON
            ]


def get_compare_url_parameters(
    operation, reference, comparison=None, upload=None, euf=False, strand=True
):
    parameters = []
    for r in reference:
        parameters.append(f"reference={r}")
    if comparison is not None:
        for r in comparison:
            parameters.append(f"comparison={r}")
    if strand:
        parameters.append("strand=true")
    else:
        parameters.append("strand=false")
    if upload is not None:
        parameters.append(f"upload={upload}")
    if euf:
        parameters.append("euf=true")
    return f"/{operation}?" + "&".join(parameters)


def get_a_datasets_as_comparison_records(*dataset_ids):
    return [
        ComparisonRecord(**r.__dict__, eufid=r.dataset_id)
        for i in dataset_ids
        for r in DATA_BY_DATASET_ID[i]
    ]


def get_b_dataset_list_as_comparison_records(*dataset_ids):
    return [
        [
            ComparisonRecord(**r.__dict__, eufid=r.dataset_id)
            for r in DATA_BY_DATASET_ID[i]
        ]
        for i in dataset_ids
    ]


@pytest.mark.parametrize(
    "reference,comparison,upload,euf,strand",
    [
        (["datasetidAxx"], ["datasetidBxx"], None, None, True),
        (["datasetidAxx", "datasetidBxx"], ["datasetidCxx"], None, None, True),
        (["datasetidAxx"], ["datasetidBxx", "datasetidCxx"], None, None, False),
        (["datasetidAxx"], None, MockFileService.VALID_TEMP_FILE_ID, False, False),
        (["datasetidBxx"], None, MockFileService.VALID_TEMP_FILE_ID, True, False),
    ],
)
def test_closest(
    test_client, comparison_services, reference, comparison, upload, euf, strand
):
    result = test_client.get(
        get_compare_url_parameters(
            "closest", reference, comparison, upload, euf, strand
        )
    )
    assert result.status == "200 OK"
    assert (
        ClosestResponse.model_validate_json(result.text).records
        == MockBedtoolsService.CLOSEST_RESULT
    )
    check_comparison_mocks("closest", reference, comparison, upload, euf, strand)


@pytest.mark.parametrize(
    "reference,comparison,upload,euf,strand",
    [
        (["datasetidAxx"], ["datasetidBxx"], None, None, True),
        (["datasetidAxx", "datasetidBxx"], ["datasetidCxx"], None, None, True),
        (["datasetidAxx"], ["datasetidBxx", "datasetidCxx"], None, None, False),
        (["datasetidAxx"], None, MockFileService.VALID_TEMP_FILE_ID, False, False),
        (["datasetidBxx"], None, MockFileService.VALID_TEMP_FILE_ID, True, False),
    ],
)
def test_subtract(
    test_client, comparison_services, reference, comparison, upload, euf, strand
):
    result = test_client.get(
        get_compare_url_parameters(
            "subtract", reference, comparison, upload, euf, strand
        )
    )
    assert result.status == "200 OK"
    assert (
        SubtractResponse.model_validate_json(result.text).records
        == MockBedtoolsService.SUBTRACT_RESULT
    )
    check_comparison_mocks("subtract", reference, comparison, upload, euf, strand)


@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "/intersect?reference=datasetidAxx&strand=true",
            400,
            "Need either a upload_id or a comparison_ids",
        ),
        (
            "/subtract?reference=datasetidAxx"
            "&comparison=datasetidBxx&comparison=datasetidCxx&comparison=datasetidDxx&comparison=datasetidExx"
            "&strand=true",
            400,
            "Parameter 'comparison contained too many dataset IDs (max. 3)",
        ),
        (
            "/closest?reference=datasetidAxx&comparison=datasetidBxx&strand=strand_aware",
            400,
            "Got bad value for parameter 'strand' (allowed: 'true', 'false')",
        ),
        (
            "/subtract?reference=datasetidAxx&upload=blubber&strand=strand_aware",
            404,
            "Temporary file not found - your upload may have expired",
        ),
    ],
)
def test_bad_url(test_client, comparison_services, url, http_status, message):
    result = test_client.get(url)
    assert result.status_code == http_status
    assert result.json["message"] == message
