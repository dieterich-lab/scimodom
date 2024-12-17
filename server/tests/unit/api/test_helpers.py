import pytest
from flask import Flask
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    get_valid_dataset,
    get_valid_taxa_id_from_string,
    get_non_negative_int,
    get_positive_int,
    get_optional_non_negative_int,
    get_optional_positive_int,
    get_valid_bam_file,
    validate_request_size,
)


@pytest.fixture
def test_client():
    app = Flask(__name__)

    @app.route("/test/<taxa_id>", methods=["GET"])
    def get_taxa_id(taxa_id):
        return taxa_id, 200

    yield app.test_client()


@pytest.fixture
def mock_services(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_dataset_service", return_value=MockDatasetService()
    )
    mocker.patch(
        "scimodom.api.helpers.get_file_service", return_value=MockFileService()
    )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )


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


# tests


# not tested:
# - get_user_with_write_permission_on_dataset

# implicitely tested in api/test_dataset_api.py:
# - get_valid_dataset_id_list_from_request_parameter
# - get_valid_tmp_file_id_from_request_parameter
# - get_valid_boolean_from_request_parameter

# implicitely tested in api/test_modification_api.py
# - get_valid_taxa_id
# - get_valid_targets_type
# - validate_rna_type
# - get_valid_coords


@pytest.mark.parametrize(
    "eufid,expected_status,expected_message",
    [
        ("ABCDEFGHIJK", 400, "Invalid dataset ID"),
        ("ABCDEFGHIJKLM", 400, "Invalid dataset ID"),
        ("AB!DEF.HIJ/L", 400, "Invalid dataset ID"),
        ("aBCDEFGHIJKL", 404, "Unknown dataset"),
    ],
)
def test_get_valid_dataset(eufid, expected_status, expected_message, mock_services):
    with pytest.raises(ClientResponseException) as exc:
        get_valid_dataset(eufid)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_message["message"] == expected_message
    assert returned_status == expected_status


def test_get_valid_taxa_from_string(test_client, mock_services):
    with test_client as client:
        response = client.get("/test/9606")
        taxa_id_as_int = get_valid_taxa_id_from_string(response.data)
        assert taxa_id_as_int == 9606


@pytest.mark.parametrize(
    "value,expected_status,expected_message",
    [(10090, 404, "Unrecognized Taxa ID"), ("X", 400, "Invalid Taxa ID")],
)
def test_get_valid_taxa_from_string_fail(
    value, expected_status, expected_message, test_client, mock_services
):
    with test_client as client:
        response = client.get(f"/test/{value}")
        with pytest.raises(ClientResponseException) as exc:
            taxa_id_as_int = get_valid_taxa_id_from_string(response.data)
        returned_message, returned_status = exc.value.response_tuple
        assert returned_message["message"] == expected_message
        assert returned_status == expected_status


@pytest.mark.parametrize(
    "value",
    ["a", -1, 1.5],
)
def test_get_non_negative_int(test_client, value):
    with test_client as client:
        response = client.get(f"/?value={value}")
        # required
        with pytest.raises(ClientResponseException) as exc:
            get_non_negative_int("value")
        returned_message, returned_status = exc.value.response_tuple
        assert returned_message["message"] == "Invalid value"
        assert returned_status == 400
        # optional
        if value != -1:
            assert get_optional_non_negative_int("value") is None
        else:
            with pytest.raises(ClientResponseException) as exc:
                get_optional_non_negative_int("value")
            returned_message, returned_status = exc.value.response_tuple
            assert returned_message["message"] == "Invalid value"
            assert returned_status == 400


@pytest.mark.parametrize(
    "value",
    ["a", 0, 1.5],
)
def test_get_positive_int(test_client, value):
    with test_client as client:
        response = client.get(f"/?value={value}")
        # required
        with pytest.raises(ClientResponseException) as exc:
            get_positive_int("value")
        returned_message, returned_status = exc.value.response_tuple
        assert returned_message["message"] == "Invalid value"
        assert returned_status == 400
        # optional
        if value != 0:
            assert get_optional_positive_int("value") is None
        else:
            with pytest.raises(ClientResponseException) as exc:
                get_optional_positive_int("value")
            returned_message, returned_status = exc.value.response_tuple
            assert returned_message["message"] == "Invalid value"
            assert returned_status == 400


@pytest.mark.parametrize(
    "bam_file,expected_status,expected_message",
    [
        ("wrong file name.bam", 400, "Invalid file name"),
        ("file_name.bam", 404, "Unknown file name and/or unknown/invalid dataset ID"),
    ],
)
def test_get_valid_bam_file(bam_file, expected_status, expected_message, mock_services):
    with pytest.raises(ClientResponseException) as exc:
        get_valid_bam_file("EUFID_IS_NOT_TESTED", bam_file)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_message["message"] == expected_message
    assert returned_status == expected_status


def test_validate_request_size(test_client):
    with test_client as client:
        response = client.post("/", data="Content-Length")
        with pytest.raises(ClientResponseException) as exc:
            validate_request_size(10)
        returned_message, returned_status = exc.value.response_tuple
        assert returned_message["message"] == "File too large (max. 10 bytes)"
        assert returned_status == 413
