from enum import Enum

import pytest
from flask import Flask
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    get_required_json_fields,
    get_required_query_param,
    get_route_param,
    validate_chrom,
    get_unique_list_from_query_param,
    get_valid_rna_type,
    get_valid_rna_type_from_route,
    get_valid_taxa_id,
    get_valid_taxa_id_from_route,
    get_valid_biotypes,
    get_valid_features,
    get_valid_coords,
    get_valid_target_type,
    get_valid_dataset,
    get_valid_selections,
    get_non_negative_int,
    get_positive_int,
    get_optional_non_negative_int,
    get_optional_positive_int,
    get_valid_bam_file,
    validate_request_size,
)
from scimodom.utils.specs.enums import Strand


@pytest.fixture
def app():
    return Flask(__name__)


# @pytest.fixture
# def test_client():
#     app = Flask(__name__)

#     @app.route("/test/<taxa_id>", methods=["GET"])
#     def get_taxa_id(taxa_id):
#         return taxa_id, 200

#     yield app.test_client()


@pytest.fixture
def mock_services(mocker):
    # mocker.patch(
    #     "scimodom.api.helpers.get_assembly_service", return_value=MockAssemblyService()
    # )
    # mocker.patch(
    #     "scimodom.api.helpers.get_dataset_service", return_value=MockDatasetService()
    # )
    # mocker.patch(
    #     "scimodom.api.helpers.get_file_service", return_value=MockFileService()
    # )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_annotation_service",
        return_value=MockAnnotationService(),
    )


class MockTargetsFileType(Enum):
    MIRNA = "mirna"
    RBP = "rbp"

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
        ("-1", 422, "Parameter 'param' must be a non-negative integer"),
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
    assert returned_status == 422
    assert returned_message["message"] == "Parameter 'param' must be a positive integer"


def test_get_optional_non_negative_int(app):
    with app.test_request_context("/", method="GET"):
        assert get_optional_non_negative_int("param") is None


def test_get_optional_positive_int(app):
    with app.test_request_context("/", method="GET"):
        assert get_optional_positive_int("param") is None


def test_get_required_query_param_missing(app):
    with app.test_request_context("/?parameter=0", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_required_query_param("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Missing required parameter: 'param'"


def test_get_required_query_param_empty(app):
    with app.test_request_context("/?param=", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_required_query_param("param")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert (
        returned_message["message"]
        == "Parameter 'param' must be a valid string (got: '')"
    )


def test_get_route_param():
    assert get_route_param("param", "param") == "param"
    assert get_route_param("param", "1", "positive_int") == 1


# tests: semantic validation


@pytest.mark.parametrize(
    "chrom,start,end,http_status,message",
    [
        ("2", None, None, 404, "chrom '2' for taxaId '9606' not found"),
        (
            "1",
            248956422,
            None,
            422,
            "Parameter 'end'/'chromEnd' must be greater than 'start'/'chromStart'",
        ),
        (
            "1",
            1,
            248956423,
            422,
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
    assert returned_message["user_message"] == "Use GET /rna_types for valid RNA types"


def test_get_valid_rna_type_from_route(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    assert get_valid_rna_type_from_route("Type1") == "Type1"


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
    assert returned_message["user_message"] == "Use GET /taxa for valid taxa"


def test_get_valid_taxa_id_from_route(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    assert get_valid_taxa_id_from_route("9606") == 9606


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
        == "Use GET biotypes/<rnaType> for valid biotypes"
    )


@pytest.mark.parametrize(
    "rna_type,http_status,message,user_message",
    [
        ("Type1", 501, "rnaType 'Type1' not implemented", None),
        (
            "Type2",
            404,
            "features 'utr' not found",
            "Use GET features/<rnaType> for valid features",
        ),
    ],
)
def test_get_valid_features_fail(
    app, mock_services, rna_type, http_status, message, user_message
):
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
                "Use GET selections for valid combinations of "
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
    with app.test_request_context("/?chrom=1&start=1&end=2&strand=a", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_coords(9606)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 422
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
    with app.test_request_context(f"/?chrom=1&start={start}&end={end}", method="GET"):
        assert get_valid_coords(9606, context=5) == result


def test_get_valid_target_type(mocker):
    mocker.patch(
        "scimodom.api.helpers.TargetsFileType",
        MockTargetsFileType,
    )
    with pytest.raises(ClientResponseException) as exc:
        get_valid_target_type(" ")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 422
    assert (
        returned_message["message"]
        == "Parameter 'targetType' must be: ['MIRNA', 'RBP']"
    )


# HERE >>>


# @pytest.mark.parametrize(
#     "eufid,expected_status,expected_message",
#     [
#         ("ABCDEFGHIJK", 400, "Invalid dataset ID"),
#         ("ABCDEFGHIJKLM", 400, "Invalid dataset ID"),
#         ("AB!DEF.HIJ/L", 400, "Invalid dataset ID"),
#         ("aBCDEFGHIJKL", 404, "Unknown dataset"),
#     ],
# )
# def test_get_valid_dataset(eufid, expected_status, expected_message, mock_services):
#     with pytest.raises(ClientResponseException) as exc:
#         get_valid_dataset(eufid)
#     returned_message, returned_status = exc.value.response_tuple
#     assert returned_message["message"] == expected_message
#     assert returned_status == expected_status


# def test_get_valid_taxa_from_string(test_client, mock_services):
#     with test_client as client:
#         response = client.get("/test/9606")
#         taxa_id_as_int = get_valid_taxa_id_from_from_route(response.data)
#         assert taxa_id_as_int == 9606


# @pytest.mark.parametrize(
#     "value,expected_status,expected_message",
#     [(10090, 404, "taxaId '10090' not found"), ("X", 400, "Invalid Taxa ID")],
# )
# def test_get_valid_taxa_from_string_fail(
#     value, expected_status, expected_message, test_client, mock_services
# ):
#     with test_client as client:
#         response = client.get(f"/test/{value}")
#         with pytest.raises(ClientResponseException) as exc:
#             taxa_id_as_int = get_valid_taxa_id_from_from_route(response.data)
#         returned_message, returned_status = exc.value.response_tuple
#         assert returned_message["message"] == expected_message
#         assert returned_status == expected_status


# @pytest.mark.parametrize(
#     "bam_file,expected_status,expected_message",
#     [
#         ("wrong file name.bam", 400, "Invalid BAM file name"),
#         ("file_name.bam", 404, "Unknown BAM file name or no association with dataset"),
#     ],
# )
# def test_get_valid_bam_file(bam_file, expected_status, expected_message, mock_services):
#     with pytest.raises(ClientResponseException) as exc:
#         get_valid_bam_file("EUFID_IS_NOT_TESTED", bam_file)
#     returned_message, returned_status = exc.value.response_tuple
#     assert returned_message["message"] == expected_message
#     assert returned_status == expected_status


# def test_validate_request_size(test_client):
#     with test_client as client:
#         response = client.post("/", data="Content-Length")
#         with pytest.raises(ClientResponseException) as exc:
#             validate_request_size(10)
#         returned_message, returned_status = exc.value.response_tuple
#         assert returned_message["message"] == "File too large (max. 10 bytes)"
#         assert returned_status == 413
