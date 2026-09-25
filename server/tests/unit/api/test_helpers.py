from enum import Enum

import pytest
from flask import Flask
from sqlalchemy.exc import NoResultFound

from scimodom.services.user import NoSuchUser
from scimodom.api.helpers import (
    ClientResponseException,
    FileTooLargeException,
    _get_required_query_param,
    get_required_json_fields,
    get_unique_list_from_query_param,
    get_non_negative_int,
    get_positive_int,
    get_optional_non_negative_int,
    get_optional_positive_int,
    get_optional_str,
    parse_non_negative_int,
    get_valid_rna_type,
    parse_valid_rna_type,
    get_valid_taxa_id,
    parse_valid_taxa_id,
    get_valid_biotypes,
    get_valid_features,
    get_valid_selections,
    get_valid_coords,
    parse_valid_target_type,
    parse_valid_sunburst_type,
    validate_chrom,
    validate_project_write_permission,
    validate_dataset_write_permission,
    get_valid_dataset,
    get_valid_bam_file,
    validate_request_size,
    get_valid_remote_file_name_from_request_parameter,
)
from scimodom.utils.specs.enums import Strand


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def mock_user_services(mocker):
    user = mocker.Mock()
    mocker.patch(
        "scimodom.api.helpers.get_jwt_identity",
        return_value="user@example.com",
    )
    mock_user_service = mocker.Mock()
    mock_user_service.get_user_by_email.return_value = user
    mocker.patch(
        "scimodom.api.helpers.get_user_service",
        return_value=mock_user_service,
    )
    mock_permission_service = mocker.Mock()
    mock_permission_service.may_change_project.return_value = True
    mock_permission_service.may_change_dataset.return_value = False
    mocker.patch(
        "scimodom.api.helpers.get_permission_service",
        return_value=mock_permission_service,
    )
    yield user, mock_user_service, mock_permission_service


class MockTargetsFileType(Enum):
    MIRNA = "mirna"
    RBP = "rbp"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))


class MockSunburstChartType(Enum):
    search = "search"
    browse = "browse"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))


class MockAnnotationService:
    # TODO MS14
    # defined independently from scalars(select(RNAType)).all()
    # see utilities_service
    VALID_RNA_TYPES = ["Type2"]

    @staticmethod
    def get_features_by_rna_type(rna_type: str):
        if rna_type not in MockAnnotationService.VALID_RNA_TYPES:
            raise NotImplementedError
        return ["exon", "intron"]


class MockAssemblyService:
    VALID_TAXA = [9606]

    @staticmethod
    def get_chroms(taxa_id: int) -> list[dict[str, str | int]]:
        if taxa_id in MockAssemblyService.VALID_TAXA:
            return [
                {"chrom": "1", "size": 248956422},
                {"chrom": "17", "size": 83257441},
            ]


class MockDatasetService:
    @staticmethod
    def get_by_id(eufid):
        if eufid != "ABCDEFGHIJKL":
            raise NoResultFound


class MockFileService:
    @staticmethod
    def get_bam_file(dataset, name):
        raise NoResultFound


class MockUtilitiesService:
    @staticmethod
    def get_rna_types():
        return [
            {"id": "Type1", "label": "Description"},
            {"id": "Type2", "label": "Description2"},
        ]

    @staticmethod
    def get_taxa():
        return [
            {
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Chordata",
            }
        ]

    @staticmethod
    def get_biotypes():
        return {"biotypes": ["biotype1", "biotype2"]}

    @staticmethod
    def get_selections():
        return [
            {
                "cls": "NGS 2nd generation",
                "cto": "HeLa",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "meth": "Chemical-assisted sequencing",
                "modification_id": 2,
                "modomics_sname": "m6A",
                "organism_id": 3,
                "rna": "WTS",
                "rna_name": "whole transcriptome",
                "selection_id": 3,
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "tech": "MePMe-seq",
                "technology_id": 2,
            },
            {
                "cls": "NGS 2nd generation",
                "cto": "HeLa",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "meth": "Enzyme/protein-assisted sequencing",
                "modification_id": 2,
                "modomics_sname": "m6A",
                "organism_id": 3,
                "rna": "WTS",
                "rna_name": "whole transcriptome",
                "selection_id": 29,
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "tech": "eTAM-seq",
                "technology_id": 7,
            },
        ]


# tests: request body validation


def test_get_required_json_fields(app):
    payload = {"field1": "value1", "field2": "value2"}
    with app.test_request_context("/", method="POST", json=payload):
        assert get_required_json_fields("field1", "field2") == payload


@pytest.mark.parametrize(
    "payload,message",
    [
        ([], "Request body must be a JSON object"),
        ({"field1": "value1"}, "Missing required field(s): field2"),
    ],
)
def test_get_required_json_fields_fail(app, payload, message):
    with app.test_request_context("/", method="POST", json=payload):
        with pytest.raises(ClientResponseException) as exc:
            get_required_json_fields("field1", "field2")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == message


# tests: syntactic validation


def test_get_non_negative_int(app):
    with app.test_request_context("/?param=1", method="GET"):
        assert get_non_negative_int("param") == 1


@pytest.mark.parametrize(
    "param,http_status,message",
    [
        ("x", 400, "Parameter 'param' must be a valid integer (got: 'x')"),
        ("-1", 400, "Parameter 'param' must be a non-negative integer"),
    ],
)
def test_get_non_negative_int_fail(app, param, http_status, message):
    with app.test_request_context(f"/?param={param}", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_non_negative_int("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == http_status
    assert returned_message["message"] == message


def test_get_positive_int_fail(app):
    with app.test_request_context("/?param=0", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_positive_int("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Parameter 'param' must be a positive integer"


def test_get_optional_non_negative_int(app):
    with app.test_request_context("/", method="GET"):
        assert get_optional_non_negative_int("param") is None


def test_get_optional_positive_int(app):
    with app.test_request_context("/", method="GET"):
        assert get_optional_positive_int("param") is None


def test_get_optional_str(app):
    with app.test_request_context("/?param=123", method="GET"):
        assert get_optional_str("param") == "123"


def test_parse_non_negative_int():
    assert parse_non_negative_int("param", "1") == 1


def test_get_required_query_param_missing(app):
    with app.test_request_context("/?parameter=0", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            _get_required_query_param("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Missing required parameter: 'param'"


def test_get_required_query_param_empty(app):
    with app.test_request_context("/?param=", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            _get_required_query_param("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert (
        returned_message["message"]
        == "Parameter 'param' must be a valid string (got: '')"
    )


# tests: semantic validation


@pytest.mark.parametrize(
    "chrom,start,end,http_status,message",
    [
        ("2", None, None, 404, "chrom '2' for taxaId '9606' not found"),
        (
            "1",
            248956422,
            None,
            400,
            "Parameter 'end'/'chromEnd' must be greater than 'start'/'chromStart'",
        ),
        (
            "1",
            1,
            248956423,
            400,
            "Parameter 'end'/'chromEnd' is greater than chrom size",
        ),
    ],
)
def test_validate_chrom_fail(mocker, chrom, start, end, http_status, message):
    mocker.patch(
        "scimodom.api.helpers.get_assembly_service", return_value=MockAssemblyService()
    )
    with pytest.raises(ClientResponseException) as exc:
        validate_chrom(9606, chrom, start, end)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == http_status
    assert returned_message["message"] == message


def test_validate_project_write_permission(mock_user_services):
    user, _, mock_permission_service = mock_user_services
    validate_project_write_permission("SMID")
    mock_permission_service.may_change_project.assert_called_once_with(
        user,
        "SMID",
    )


def test_validate_permission_on_project_forbidden(mock_user_services):
    _, _, mock_permission_service = mock_user_services
    mock_permission_service.may_change_project.return_value = False
    with pytest.raises(ClientResponseException) as exc:
        validate_project_write_permission("SMID")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 403
    assert returned_message["message"] == "Forbidden to access project 'SMID'"


def test_validate_project_write_permission_not_found(mock_user_services):
    _, mock_user_service, _ = mock_user_services
    mock_user_service.get_user_by_email.side_effect = NoSuchUser
    with pytest.raises(ClientResponseException) as exc:
        validate_project_write_permission("SMID")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 404
    assert returned_message["message"] == "User 'user@example.com' not found"


def test_validate_dataset_write_permission_forbidden(mock_user_services, dataset):
    with pytest.raises(ClientResponseException) as exc:
        validate_dataset_write_permission(dataset[0])
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 403
    assert returned_message["message"] == "Forbidden to access dataset 'dataset_id01'"


# tests: helpers


@pytest.mark.parametrize(
    "url,ltype,result",
    [
        ("/?param[]=a&param[]=b", str, ["a", "b"]),
        ("/?param=1&param[]=1", int, [1]),
        ("/?parameter=a", str, []),
    ],
)
def test_get_unique_list_from_query_param(app, url, ltype, result):
    with app.test_request_context(url, method="GET"):
        # order is not guaranteed
        assert set(get_unique_list_from_query_param("param", ltype)) == set(result)


def test_get_valid_rna_type_fail(app, mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context("/?rnaType=type1", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_rna_type()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 404
    assert returned_message["message"] == "rnaType 'type1' not found"
    assert (
        returned_message["user_message"]
        == "Use GET /catalogs/rna-types for valid RNA types"
    )


def test_parse_valid_rna_type(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    assert parse_valid_rna_type("Type1") == "Type1"


def test_get_valid_taxa_id_fail(app, mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context("/?taxaId=10090", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_taxa_id()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 404
    assert returned_message["message"] == "taxaId '10090' not found"
    assert returned_message["user_message"] == "Use GET /catalogs/taxa for valid taxa"


def test_parse_valid_taxa_id(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    assert parse_valid_taxa_id("9606") == 9606


def test_get_valid_biotypes_fail(app, mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context("/?rnaType=Type1&biotypes=biotype3", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_biotypes()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 404
    assert returned_message["message"] == "biotypes 'biotype3' not found"
    assert (
        returned_message["user_message"]
        == "Use GET /catalogs/rna-types/<rnaType>/biotypes for valid biotypes"
    )


@pytest.mark.parametrize(
    "rna_type,http_status,message,user_message",
    [
        ("Type1", 501, "rnaType 'Type1' not implemented", None),
        (
            "Type2",
            404,
            "features 'utr' not found",
            "Use GET /catalogs/rna-types/<rnaType>/features for valid features",
        ),
    ],
)
def test_get_valid_features_fail(
    app, mocker, rna_type, http_status, message, user_message
):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_annotation_service",
        return_value=MockAnnotationService(),
    )
    with app.test_request_context(f"/?rnaType={rna_type}&features=utr", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_features()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == http_status
    assert returned_message["message"] == message
    if user_message is not None:
        assert returned_message["user_message"] == user_message


@pytest.mark.parametrize(
    "part,http_status,message,user_message",
    [
        ("", 400, "Missing required parameter: 'technology'", None),
        (
            "&technology=1&technology=2",
            404,
            ("(modification, organism, technology) '(2, 3, 1)' not found."),
            (
                "Use GET /catalogs/selections for valid combinations of "
                "modification, organism, and technology identifiers"
            ),
        ),
    ],
)
def test_get_valid_selections_fail(
    app, mocker, part, http_status, message, user_message
):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context(f"/?modification=2&organism=3{part}", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_selections()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == http_status
    assert returned_message["message"] == message
    if user_message is not None:
        assert returned_message["user_message"] == user_message


def test_get_valid_coords_fail(app, mocker):
    mocker.patch(
        "scimodom.api.helpers.get_assembly_service",
        return_value=MockAssemblyService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context(
        "/?chrom=1&start=1&end=2&strand=a&taxaId=9606", method="GET"
    ):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_coords()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Parameter 'strand' must be +, -, or ."


@pytest.mark.parametrize(
    "start,end,result",
    [
        (1, 2, ("1", 0, 7, Strand("."))),
        (248956421, 248956422, ("1", 248956416, 248956422, Strand("."))),
    ],
)
def test_get_valid_coords(app, mocker, start, end, result):
    mocker.patch(
        "scimodom.api.helpers.get_assembly_service",
        return_value=MockAssemblyService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    with app.test_request_context(
        f"/?chrom=1&start={start}&end={end}&taxaId=9606", method="GET"
    ):
        assert get_valid_coords(context=5) == result


def test_parse_valid_target_type(mocker):
    mocker.patch(
        "scimodom.api.helpers.TargetsFileType",
        MockTargetsFileType,
    )
    with pytest.raises(ClientResponseException) as exc:
        parse_valid_target_type(" ")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Parameter 'target' must be: ['MIRNA', 'RBP']"


def test_parse_valid_sunburst_type(mocker):
    mocker.patch(
        "scimodom.api.helpers.SunburstChartType",
        MockSunburstChartType,
    )
    with pytest.raises(ClientResponseException) as exc:
        parse_valid_sunburst_type(" ")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert (
        returned_message["message"]
        == "Parameter 'sunburstType' must be: ['search', 'browse']"
    )


@pytest.mark.parametrize(
    "eufid,expected_status,expected_message",
    [
        ("ABCDEFGHIJKLM", 400, "Invalid datasetId 'ABCDEFGHIJKLM'"),
        ("AB!DEF.HIJ/L", 400, "Invalid datasetId 'AB!DEF.HIJ/L'"),
        ("aBCDEFGHIJKL", 404, "Dataset 'aBCDEFGHIJKL' not found"),
    ],
)
def test_get_valid_dataset(eufid, expected_status, expected_message, mocker):
    mocker.patch(
        "scimodom.api.helpers.get_dataset_service", return_value=MockDatasetService()
    )
    with pytest.raises(ClientResponseException) as exc:
        get_valid_dataset(eufid)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_message["message"] == expected_message
    assert returned_status == expected_status


@pytest.mark.parametrize(
    "bam_file,expected_status,expected_message",
    [
        ("wrong file name.bam", 400, "Invalid BamName 'wrong file name.bam'"),
        (
            "file_name.bam",
            404,
            "BAM file 'file_name.bam' not found or no association with dataset 'dataset_id01'",
        ),
    ],
)
def test_get_valid_bam_file(
    bam_file, expected_status, expected_message, mocker, dataset
):
    mocker.patch(
        "scimodom.api.helpers.get_file_service", return_value=MockFileService()
    )
    with pytest.raises(ClientResponseException) as exc:
        get_valid_bam_file(dataset[0], bam_file)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_message["message"] == expected_message
    assert returned_status == expected_status


@pytest.mark.parametrize(
    "content_length, max_size, should_raise",
    [
        (None, 100, False),  # no Content-Length
        (0, 100, False),  # empty body
        (50, 100, False),  # under the limit
        (100, 100, False),  # exactly at the limit
        (101, 100, True),  # one byte over
    ],
)
def test_validate_request_size(app, content_length, max_size, should_raise):
    kwargs = {}
    if content_length is not None:
        kwargs["data"] = b"x" * content_length

    with app.test_request_context(method="POST", path="", **kwargs):
        if should_raise:
            with pytest.raises(FileTooLargeException):
                validate_request_size(max_size=max_size)
        else:
            validate_request_size(max_size=max_size)


# tested indirectly in test_comparison_api
# - get_valid_dataset_id_list_from_request_parameter
# - get_valid_tmp_file_id_from_request_parameter


@pytest.mark.parametrize(
    "param,name,expected",
    [
        ("param", "abc123.bed", "abc123.bed"),
        ("param", "a+ bc1/23.bed", "a??bc1?23.bed"),
        ("parameter", "abc123.bed", "uploaded file"),
    ],
)
def test_get_valid_remote_file_name_from_request_parameter(app, param, name, expected):
    with app.test_request_context(f"/?{param}={name}", method="GET"):
        assert get_valid_remote_file_name_from_request_parameter("param") == expected
