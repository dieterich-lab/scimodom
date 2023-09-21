import pytest


def _get_header(variant=False):
    from io import StringIO

    from scimodom.services.importer.importer import specsEUF

    specs = specsEUF.copy()

    fmt = specs.pop("format")
    _ = specs.pop("header")
    _ = specs.pop("delimiter")
    version = next(iter(specs))
    if variant:
        fmt = fmt.lower()

    csvString = f"#fileformat={fmt}v{version}"
    csvStringIO = StringIO(csvString)
    return csvStringIO


@pytest.mark.parametrize(
    "project,variant",
    [
        ("_get_header", False),
        ("_get_header", True),
    ],
)
def test_base_importer_readEUF_header(project, variant):
    # scratch - test only reading format
    # but now we read remaining headers...

    from scimodom.services.importer.importer import BaseImporter

    importer = BaseImporter("csvStringIO", _get_header(variant))
    importer._read_version()
