import pytest

from scimodom.utils.utils import gen_short_uuid


def test_gen_short_uuid_length():
    assert len(gen_short_uuid(12, [])) == 12


def test_gen_short_uuid_avoids_existing(mocker):
    # first draw collides, second one must be a new draw
    mocker.patch(
        "scimodom.utils.utils.shortuuid.encode", side_effect=["AAAA1", "BBBB2"]
    )
    assert gen_short_uuid(5, ["AAAA1"]) == "BBBB2"


def test_gen_short_uuid_exhausted(mocker):
    mocker.patch("scimodom.utils.utils.shortuuid.encode", return_value="AAAA1")
    with pytest.raises(RuntimeError, match="after 10 attempts"):
        gen_short_uuid(5, ["AAAA1"], max_attempts=10)
