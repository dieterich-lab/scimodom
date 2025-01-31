from pathlib import Path

import pytest
from flask import Flask

from scimodom.database.models import Assembly
from scimodom.cli.assembly import assembly_cli
from scimodom.services.assembly import AssemblyService
from scimodom.services.external import ExternalService
from scimodom.services.file import FileService
from scimodom.services.web import WebService
from tests.mocks.enums import MockEnsembl


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_assembly_service(Session, tmp_path):
    return AssemblyService(
        session=Session(),
        external_service=ExternalService(
            file_service=_get_file_service(Session, tmp_path)
        ),
        web_service=WebService(),
        file_service=_get_file_service(Session, tmp_path),
    )


@pytest.fixture
def test_runner():
    app = Flask(__name__)
    app.register_blueprint(assembly_cli)
    yield app.test_cli_runner()


@pytest.fixture
def mock_services(mocker, Session, tmp_path):
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    mocker.patch(
        "scimodom.cli.assembly.get_assembly_service",
        return_value=_get_assembly_service(Session, tmp_path),
    )


# tests
# Success relies on successful download from Ensembl;
# the test asserts if files are there, but not their content.
# DO NOT run this test under the test suite!


def test_add_assembly(Session, tmp_path, test_runner, setup, mock_services):
    result = test_runner.invoke(args=["assembly", "add", "1"], input="y")
    # exceptions are handled gracefully so exit code will likely always be 0...
    assert result.exit_code == 0

    with Session() as session:
        assert session.query(Assembly).count() == 6

    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens"
    for assembly in ["GRCh37", "NCBI34", "NCBI35", "NCBI36"]:
        assert Path(d, assembly, f"{assembly}_to_GRCh38.chain.gz").is_file()
    chroms = [str(c) for c in range(1, 23)]
    chroms.extend(["X", "Y", "MT"])
    for chrom in chroms:
        for ext in ["", ".fai", ".gzi"]:
            assert Path(
                d, "GRCh38", f"Homo_sapiens.GRCh38.dna.chromosome.{chrom}.fa.gz{ext}"
            ).is_file()
    assert Path(d, "GRCh38", "info.json").is_file()
    assert Path(d, "GRCh38", "release.json").is_file()
    assert Path(d, "GRCh38", "chrom.sizes").is_file()
