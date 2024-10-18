from scimodom.utils.specs.euf import EUF


def test_euf_version():
    LATEST_VERSION = "1.8"
    assert EUF["versions"][-1] == LATEST_VERSION
