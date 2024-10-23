from io import StringIO, BytesIO
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


# tests


# Annotation


def test_get_annotation_dir(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_dir(9606) == Path(
        tmp_path, "t_data", "annotation", "Homo_sapiens", "GRCh38"
    )


# Cache


def test_gene_cache(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    service.update_gene_cache(122, ["1", "2", "Y"])
    service.update_gene_cache(123, ["1", "3"])
    service.update_gene_cache(124, ["1", "3", "X"])
    assert set(service.get_gene_cache([122, 123])) == set(["1", "2", "3", "Y"])
    service.update_gene_cache(123, ["1", "15"])
    assert set(service.get_gene_cache([122, 123])) == set(["1", "2", "15", "Y"])
    service.delete_gene_cache(124)
    with pytest.raises(FileNotFoundError):
        service.get_gene_cache([124])


def test_sunburst_cache(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)

    def update_cache():
        def generator():
            yield "cache content"

        service.update_sunburst_cache("chart", generator())

    service.run_sunburst_update(update_cache)
    with service.open_sunburst_cache("chart") as fh:
        assert fh.read() == "cache content"


# Project


def test_project_files(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    with service.create_project_metadata_file("SMID") as fh:
        pass
    service.delete_project_metadata_file("SMID")
    with service.create_project_request_file("UUID") as fh:
        fh.write("request")
    with service.open_project_request_file("UUID") as fh:
        assert fh.read() == "request"
    service.delete_project_request_file("UUID")


# Assembly


def test_get_assembly_file_path_for_chrom(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_assembly_file_path(9606, AssemblyFileType.CHROM) == Path(
        tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh38", "chrom.sizes"
    )


def test_get_assembly_file_path_for_chain(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_assembly_file_path(
        9606,
        AssemblyFileType.CHAIN,
        chain_file_name="chain",
        chain_assembly_name="GRCh37",
    ) == Path(tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh37", "chain")


def test_get_assembly_file_path_for_chain_fail(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(ValueError) as exc:
        assert service.get_assembly_file_path(
            9606, AssemblyFileType.CHAIN, chain_file_name="chain"
        )
    assert (str(exc.value)) == "Missing chain_file_name and/or assembly_name!"


def test_get_assembly_file_path_for_dna(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    # cf. AssemblyFileType (specs.enums) for file name template
    assert service.get_assembly_file_path(
        9606, AssemblyFileType.DNA, chrom="1"
    ) == Path(
        tmp_path,
        "t_data",
        "assembly",
        "Homo_sapiens",
        "GRCh38",
        "Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz",
    )


def test_get_assembly_file_path_for_dna_fail(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(ValueError) as exc:
        assert service.get_assembly_file_path(9606, AssemblyFileType.DNA)
    assert (str(exc.value)) == "Missing chrom!"


@pytest.mark.parametrize(
    "file_type",
    [AssemblyFileType.CHROM, AssemblyFileType.INFO, AssemblyFileType.RELEASE],
)
def test_create_assembly_file(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with service.create_assembly_file(9606, file_type) as fh:
        fh.write("info")
    with service.open_assembly_file(9606, file_type) as fh:
        assert fh.read() == "info"


@pytest.mark.parametrize("file_type", [AssemblyFileType.DNA, AssemblyFileType.CHAIN])
def test_create_assembly_file_fail(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(NotImplementedError):
        service.create_assembly_file(9606, file_type)


@pytest.mark.parametrize("file_type", [AssemblyFileType.DNA, AssemblyFileType.CHAIN])
def test_open_assembly_file_fail(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(NotImplementedError):
        service.open_assembly_file(9606, file_type)


def test_create_chain_file(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with service.create_chain_file(9606, "chain", "GRCh37") as fh:
        fh.write(b"bla")
    path = Path(tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh37", "chain")
    with open(path, "rb") as fh:
        assert fh.read() == b"bla"


def test_delete_assembly(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    service.create_assembly_file(9606, AssemblyFileType.INFO)
    assert service.check_if_assembly_exists(9606, "GRCh38") is True
    service.delete_assembly(9606, "GRCh38")
    assert service.check_if_assembly_exists(9606, "GRCh38") is False


#  Files


def test_upload(Session, tmp_path):
    stream = BytesIO(b"some bedrmod data")
    service = _get_file_service(Session, tmp_path)
    file_id = service.upload_tmp_file(stream, 1024)
    assert service.check_tmp_upload_file_id(file_id) is True
    with service.open_tmp_upload_file_by_id(file_id) as fh:
        assert fh.read() == "some bedrmod data"


# BAM


# vars


def test_count_lines(Session, tmp_path):
    test_file = Path(tmp_path, "example.txt")
    test_file.write_text("line1\nline2\nline3\n")
    service = _get_file_service(Session, tmp_path)
    assert service.count_lines(test_file) == 3
