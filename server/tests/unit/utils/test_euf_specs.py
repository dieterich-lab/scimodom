from scimodom.utils.specs.euf import EUF_VERSION, EUF_COMPATIBLE_VERSIONS


def test_euf_version():
    LATEST_VERSION = "1.8"
    COMPATIBLE_VERSIONS = ["1.8"]
    assert EUF_VERSION == LATEST_VERSION
    assert EUF_COMPATIBLE_VERSIONS == COMPATIBLE_VERSIONS
