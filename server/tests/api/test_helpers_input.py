from enum import Enum

import pytest
from flask import Flask

from scimodom.api.helpers import (
    ClientResponseException,
    FileTooLargeException,
    get_non_negative_int,
    get_optional_non_negative_int,
    get_positive_int,
    get_optional_positive_int,
    get_optional_str,
    get_optional_bool,
    get_required_list,
    get_optional_list,
    get_valid_target_type,
    get_valid_file_name,
    validate_file_name,
    parse_valid_sunburst_type,
    get_required_json_fields,
    validate_request_size,
    _get_required_query_param,
    _is_valid_identifier,
    _validate_file_name,
)


@pytest.fixture
def app():
    return Flask(__name__)


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


# tests: query parameter parsing/conversion


def test_get_non_negative_int(app):
    with app.test_request_context("/?param=1", method="GET"):
        assert get_non_negative_int("param") == 1


@pytest.mark.parametrize(
    "param,http_status,message",
    [
        ("x", 400, "Parameter 'param' must be a valid _non_negative_int (got: 'x')"),
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


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("true", True),
        ("false", False),
        ("TRUE", True),
        ("FALSE", False),
        ("True", True),
        ("False", False),
        ("tRuE", True),
        ("FaLsE", False),
    ],
)
def test_get_optional_bool_case(app, raw, expected):
    with app.test_request_context(f"/?strand={raw}"):
        assert get_optional_bool("strand") is expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "1",
        "0",
        "truthy",
        "falsey",
        " true",  # leading space is not trimmed
        "true ",  # trailing space is not trimmed
    ],
)
def test_get_optional_bool_invalid_values(app, raw):
    with app.test_request_context(f"/?strand={raw}"):
        with pytest.raises(ClientResponseException) as exc:
            get_optional_bool("strand")
    returned_message, returned_status = exc.value.response_tuple
    assert (
        returned_message["message"]
        == f"Invalid value for 'strand' (allowed: 'true', 'false', got: '{raw}')"
    )
    assert returned_status == 400


@pytest.mark.parametrize(
    "url,ltype,result",
    [
        ("/?param[]=a&param[]=b", str, []),
        ("/?param=1&param=2", int, [1, 2]),
        ("/?param=a&param=b", str, ["a", "b"]),
    ],
)
def test_get_optional_list(app, url, ltype, result):
    with app.test_request_context(url, method="GET"):
        assert get_optional_list("param", ltype) == result


@pytest.mark.parametrize(
    "url,ltype,message",
    [
        ("/?param=a&param=2", int, "Parameter 'param' must be a valid int (got: 'a')"),
        (
            "/?param=a&param=",
            str,
            "Parameter 'param' must be a valid non-empty str (got: '')",
        ),
        ("/?", str, "Missing required parameter: 'param'"),
    ],
)
def test_get_required_list_fail(app, url, ltype, message):
    with app.test_request_context(url, method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            assert get_required_list("param", ltype)
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == message


def test_get_valid_target_type(app, mocker):
    mocker.patch(
        "scimodom.api.helpers.input.TargetsFileType",
        MockTargetsFileType,
    )
    with app.test_request_context("/?target= ", method="GET"):
        with pytest.raises(ClientResponseException) as exc:
            get_valid_target_type()
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert (
        returned_message["message"]
        == "Invalid value for 'target' (allowed: ['MIRNA', 'RBP'], got: ' ')"
    )


@pytest.mark.parametrize(
    "param,name,expected",
    [
        ("param", "abc123.bed", "abc123.bed"),
        ("param", "a+ bc1/23.bed", "a??bc1?23.bed"),
        (
            "param",
            "vSv4hiwvi98rb7X6agV260QQQwlJ2dgwTFm46AuALUQMEFDOSlQ0gN7p6lXeJ42dMXuL2g4lYJNCE59PRLEJyiZhrYY7B3W7aFO5P0y8gW1D1R3TICyUqk6flBS75CMGp1Mkb1MM2dkBrAb2OZrHzR6sw9M4AGV4ST0Kt8RYBBd08O9IBdcZR0CjGQCD5LVFeeqIBPXW6PXPiUkaX57RU4P0Gf1uC8hK69n10uugm6dJ104WKqA2pdJG8mgfv3c0zO843168m8r7sip90Y1r3sJHX5uL16dER",
            "vSv4hiwvi98rb7X6agV260QQQwlJ2dgwTFm46AuALUQMEFDOSlQ0gN7p6lXeJ42dMXuL2g4lYJNCE59PRLEJyiZhrYY7B3W7aFO5P0y8gW1D1R3TICyUqk6flBS75CMGp1Mkb1MM2dkBrAb2OZrHzR6sw9M4AGV4ST0Kt8RYBBd08O9IBdcZR0CjGQCD5LVFeeqIBPXW6PXPiUkaX57RU4P0Gf1uC8hK69n10uugm6dJ104WKqA2pdJG8mgfv3c0",
        ),
        ("parameter", "any name!", "upload"),
    ],
)
def test_get_valid_file_name(app, param, name, expected):
    with app.test_request_context(f"/?param={name}", method="GET"):
        assert get_valid_file_name(param) == expected


def test_parse_and_validate_file_name():
    with pytest.raises(ClientResponseException) as exc:
        validate_file_name("BAM", "wrong file name.bam")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_message["message"] == "Invalid BAM file name: 'wrong file name.bam'"
    assert returned_status == 400


def test_parse_valid_sunburst_type(mocker):
    mocker.patch(
        "scimodom.api.helpers.input.SunburstChartType",
        MockSunburstChartType,
    )
    with pytest.raises(ClientResponseException) as exc:
        parse_valid_sunburst_type(" ")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert (
        returned_message["message"]
        == "Invalid value for 'sunburstType' (allowed: ['search', 'browse'], got: ' ')"
    )


# tests: JSON body parsing/structural validation


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


def test_get_required_json_fields(app):
    payload = {"field1": "value1", "field2": "value2"}
    with app.test_request_context("/", method="POST", json=payload):
        assert get_required_json_fields("field1", "field2") == payload


# tests: request size validation


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


# tests


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
        == "Parameter 'param' must be a valid _non_empty_str (got: '')"
    )


def test_is_valid_identifer():
    assert _is_valid_identifier("asdf568FAF", 10) is True
    assert _is_valid_identifier("asdf568FA", 5) is False


def test_validate_file_name(app):
    assert _validate_file_name("NAME", "a-good_name,123.txt") is None


def test_validate_file_name_fail(app):
    with pytest.raises(ClientResponseException) as exc:
        _validate_file_name("NAME", "bad name.txt")
    returned_message, returned_status = exc.value.response_tuple
    assert returned_status == 400
    assert returned_message["message"] == "Invalid NAME file name: 'bad name.txt'"
