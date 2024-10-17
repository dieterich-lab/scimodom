from pathlib import Path

import pytest

from scimodom.services.file import FileService
from scimodom.utils.specs.enums import AssemblyFileType


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def test_get_assembly_file_path_for_chrom(Session, tmp_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_file_service(Session, tmp_path)
    assert service.get_assembly_file_path(9606, AssemblyFileType.CHROM) == Path(
        tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh38", "chrom.sizes"
    )


def test_get_assembly_file_path_for_chain(Session, tmp_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_file_service(Session, tmp_path)
    assert service.get_assembly_file_path(
        9606,
        AssemblyFileType.CHAIN,
        chain_file_name="chain",
        chain_assembly_name="GRCh37",
    ) == Path(tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh37", "chain")


def test_get_assembly_file_path_for_chain_fail(Session, tmp_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(ValueError) as exc:
        assert service.get_assembly_file_path(
            9606, AssemblyFileType.CHAIN, chain_file_name="chain"
        )
    assert (str(exc.value)) == "Missing chain_file_name and/or assembly_name!"


def test_create_chain_file(Session, tmp_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_file_service(Session, tmp_path)
    with service.create_chain_file(9606, "chain", "GRCh37") as fh:
        fh.write(b"bla")
    path = Path(tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh37", "chain")
    with open(path, "rb") as fh:
        assert fh.read() == b"bla"


def test_count_lines(Session, tmp_path):
    test_file = Path(tmp_path, "example.txt")
    test_file.write_text("line1\nline2\nline3\n")
    service = _get_file_service(Session, tmp_path)
    assert service.count_lines(test_file) == 3


def test_get_annotation_path(Session, tmp_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_dir(9606) == Path(
        tmp_path, "t_data", "annotation", "Homo_sapiens", "GRCh38"
    )


def test_update_gene_cache(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    service.update_gene_cache(122, ["1", "2", "Y"])
    service.update_gene_cache(123, ["1", "3"])
    service.update_gene_cache(124, ["1", "3", "X"])
    assert set(service.get_gene_cache([122, 123])) == set(["1", "2", "3", "Y"])
    service.update_gene_cache(123, ["1", "15"])
    assert set(service.get_gene_cache([122, 123])) == set(["1", "2", "15", "Y"])
