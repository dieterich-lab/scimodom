from scimodom.utils.specs.euf import EUF_VERSION


def test_euf_version():
    LATEST_VERSION = "1.8"
    assert EUF_VERSION == LATEST_VERSION
