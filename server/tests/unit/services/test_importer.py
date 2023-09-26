import pytest


def _get_header(variant=False):
    from io import StringIO
    from scimodom.services.importer import specsEUF

    specs = specsEUF.copy()
    fmt = specs.pop("format")
    _ = specs.pop("header")
    _ = specs.pop("delimiter")
    version = next(iter(specs))
    expected_version = f"{fmt}v{version}"
    if variant:
        fmt = fmt.lower()
    csvString = f"#fileformat={fmt}v{version}"
    csvStringIO = StringIO(csvString)
    return expected_version, csvStringIO


@pytest.mark.parametrize(
    "project,variant",
    [
        ("_get_header", False),
        ("_get_header", True),
    ],
)
def test_importer_read_version(Session, project, variant):
    from scimodom.services.importer import EUFImporter

    version, handle = _get_header(variant)
    # temporarily...
    importer = EUFImporter(
        Session(),
        "csvStringIO",
        handle,
        "ABCDEFGH",
        "123456789ABC",
        "Title",
        9606,
        1,
        False,
    )
    importer._read_version()
    assert version == importer._version
