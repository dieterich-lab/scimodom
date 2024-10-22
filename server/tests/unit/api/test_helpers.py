import pytest
from flask import Flask
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    get_valid_dataset,
    get_non_negative_int,
    get_positive_int,
    get_optional_non_negative_int,
    get_optional_positive_int,
)


@pytest.fixture
def test_client():
    app = Flask(__name__)
    yield app.test_client()


@pytest.fixture
def helpers_services(mocker):
    mocker.patch(
        "scimodom.api.helpers.get_dataset_service", return_value=MockDatasetService()
    )


class MockDatasetService:
    @staticmethod
    def get_by_id(eufid):
        if eufid != "ABCDEFGHIJKL":
            raise NoResultFound


# tests


# implicitely tested in api/test_bam_file.py:
# - get_user_with_write_permission_on_dataset
# - get_valid_bam_file
# - validate_request_size

# implicitely tested in api/test_dataset_api.py:
# - get_valid_dataset_id_list_from_request_parameter
# - get_valid_tmp_file_id_from_request_parameter
# - get_valid_boolean_from_request_parameter

# implicitely tested in api/test+modification_api.py
# - get_valid_taxa_id
# - get_valid_targets_type
# - validate_rna_type
# - get_valid_coords(


@pytest.mark.parametrize(
    "eufid,expected_status,expected_message",
    [
        ("ABCDEFGHIJK", 400, "Invalid dataset ID"),
        ("ABCDEFGHIJKLM", 400, "Invalid dataset ID"),
        ("AB!DEF.HIJ/L", 400, "Invalid dataset ID"),
        ("aBCDEFGHIJKL", 404, "Unknown dataset"),
    ],
)
def test_get_valid_dataset(eufid, expected_status, expected_message, helpers_services):
    with pytest.raises(ClientResponseException) as exc:
        get_valid_dataset(eufid)
    returned_message, returned_status = exc.value.response_tupel
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
        returned_message, returned_status = exc.value.response_tupel
        assert returned_message["message"] == "Invalid value"
        assert returned_status == 400
        # optional
        if value != -1:
            assert get_optional_non_negative_int("value") is None
        else:
            with pytest.raises(ClientResponseException) as exc:
                get_optional_non_negative_int("value")
            returned_message, returned_status = exc.value.response_tupel
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
        returned_message, returned_status = exc.value.response_tupel
        assert returned_message["message"] == "Invalid value"
        assert returned_status == 400
        # optional
        if value != 0:
            assert get_optional_positive_int("value") is None
        else:
            with pytest.raises(ClientResponseException) as exc:
                get_optional_positive_int("value")
            returned_message, returned_status = exc.value.response_tupel
            assert returned_message["message"] == "Invalid value"
            assert returned_status == 400
