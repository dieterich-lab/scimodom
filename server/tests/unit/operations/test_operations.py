import pytest


def _get_records():
    a = [
        ("1", 101, 102, "m6A", 1, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 199, 200, "m6A", 2, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 200, 201, "m6A", 3, "+", "KEyK5s3pcKjE", 0, 0),
        ("1", 299, 300, "m6A", 4, "-", "KEyK5s3pcKjE", 0, 0),
        ("1", 599, 600, "m6A", 5, "+", "KEyK5s3pcKjE", 0, 0),
    ]
    b = [
        ("1", 1, 2, "m6A", 6, "+", "FCfhtbEJpbvR", 0, 0),
        ("1", 199, 200, "m6A", 7, "+", "FCfhtbEJpbvR", 0, 0),
        ("1", 299, 300, "m6A", 8, "+", "FCfhtbEJpbvR", 0, 0),
    ]
    c = [
        ("1", 97, 102, "m6A", 9, "+", "3HsmkimcHAFA", 0, 0),
        ("1", 197, 202, "m6A", 10, "+", "3HsmkimcHAFA", 0, 0),
        ("1", 295, 300, "m6A", 11, "-", "3HsmkimcHAFA", 0, 0),
        ("1", 1, 6, "m6A", 12, "+", "3HsmkimcHAFA", 0, 0),
    ]
    # pybedtools defaults score to str, as well as all other fields beyond BED6
    intersect = [
        (
            "1",
            101,
            102,
            "m6A",
            "1",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "97",
            "102",
            "m6A",
            "9",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            199,
            200,
            "m6A",
            "2",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "199",
            "200",
            "m6A",
            "7",
            "+",
            "FCfhtbEJpbvR",
            "0",
            "0",
        ),
        (
            "1",
            199,
            200,
            "m6A",
            "2",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "197",
            "202",
            "m6A",
            "10",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            200,
            201,
            "m6A",
            "3",
            "+",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "197",
            "202",
            "m6A",
            "10",
            "+",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
        (
            "1",
            299,
            300,
            "m6A",
            "4",
            "-",
            "KEyK5s3pcKjE",
            "0",
            "0",
            "1",
            "295",
            "300",
            "m6A",
            "11",
            "-",
            "3HsmkimcHAFA",
            "0",
            "0",
        ),
    ]

    return a, [b, c], intersect


def test_get_intersect():
    from scimodom.utils.operations import get_op

    a_records, b_records, expected_records = _get_records()
    records = get_op("intersect")(a_records, b_records)

    assert records == expected_records
