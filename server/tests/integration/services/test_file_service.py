from io import BytesIO
from pathlib import Path

import pytest
from sqlalchemy import select, func

from scimodom.database.models import BamFile
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
    assert service.get_gene_cache(122) == ["1", "2", "Y"]
    assert service.get_gene_cache(123) == ["1", "3"]
    service.update_gene_cache(123, ["1", "15"])
    assert service.get_gene_cache(123) == ["1", "15"]
    service.delete_gene_cache(124)
    with pytest.raises(FileNotFoundError):
        service.get_gene_cache(124)


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
# cf. AssemblyFileType (specs.enums)


def test_get_assembly_file_path_for_common(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    for file_type in AssemblyFileType.common():
        assert service.get_assembly_file_path(9606, file_type) == Path(
            tmp_path, "t_data", "assembly", "Homo_sapiens", "GRCh38", file_type.value
        )


def test_get_assembly_file_path_for_chain(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_assembly_file_path(
        9606,
        AssemblyFileType.CHAIN,
        assembly_name="GRCh37",
    ) == Path(
        tmp_path,
        "t_data",
        "assembly",
        "Homo_sapiens",
        "GRCh37",
        AssemblyFileType.CHAIN.value(
            source_assembly="GRCh37", target_assembly="GRCh38"
        ),
    )


def test_get_assembly_file_path_for_chain_fail(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(ValueError) as exc:
        assert service.get_assembly_file_path(9606, AssemblyFileType.CHAIN)
    assert (str(exc.value)) == "Missing required assembly_name."


def test_get_assembly_file_path_for_fasta(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    for file_type in AssemblyFileType.fasta():
        assert service.get_assembly_file_path(9606, file_type, chrom="1") == Path(
            tmp_path,
            "t_data",
            "assembly",
            "Homo_sapiens",
            "GRCh38",
            file_type.value(organism="Homo_sapiens", assembly="GRCh38", chrom=1),
        )


def test_get_assembly_file_path_for_fasta_fail(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(ValueError) as exc:
        assert service.get_assembly_file_path(9606, AssemblyFileType.DNA)
    assert (str(exc.value)) == "Missing required chrom."


@pytest.mark.parametrize(
    "file_type",
    [AssemblyFileType.CHROM, AssemblyFileType.INFO, AssemblyFileType.RELEASE],
)
def test_create_and_open_assembly_file(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with service.create_assembly_file(9606, file_type) as fh:
        fh.write("info")
    with service.open_assembly_file(9606, file_type) as fh:
        assert fh.read() == "info"


@pytest.mark.parametrize(
    "file_type", AssemblyFileType.fasta() + (AssemblyFileType.CHAIN,)
)
def test_create_assembly_file_fail(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(NotImplementedError):
        service.create_assembly_file(9606, file_type)


@pytest.mark.parametrize(
    "file_type", AssemblyFileType.fasta() + (AssemblyFileType.CHAIN,)
)
def test_open_assembly_file_fail(Session, tmp_path, setup, file_type):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(NotImplementedError):
        service.open_assembly_file(9606, file_type)


def test_create_chain_file(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with service.create_chain_file(9606, "GRCh37") as fh:
        fh.write(b"bla")
    path = Path(
        tmp_path,
        "t_data",
        "assembly",
        "Homo_sapiens",
        "GRCh37",
        AssemblyFileType.CHAIN.value(
            source_assembly="GRCh37", target_assembly="GRCh38"
        ),
    )
    with open(path, "rb") as fh:
        assert fh.read() == b"bla"


def test_delete_current_assembly_and_check_if_exists(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    service.create_assembly_file(9606, AssemblyFileType.INFO)
    service.create_assembly_file(9606, AssemblyFileType.RELEASE)
    with service.create_assembly_file(9606, AssemblyFileType.CHROM) as fh:
        fh.write("1\t248956422\n")
    # TODO create fasta files
    for file_type in AssemblyFileType.fasta():
        service.get_assembly_file_path(9606, file_type, chrom="1").touch()
    assert service.check_if_assembly_exists(9606) is True
    service.delete_assembly(9606, "GRCh38")
    assert service.check_if_assembly_exists(9606) is False


def test_delete_assembly_and_check_if_exists(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    service.create_chain_file(9606, "GRCh37")
    assert service.check_if_assembly_exists(9606, "GRCh37") is True
    service.delete_assembly(9606, "GRCh37")
    assert service.check_if_assembly_exists(9606, "GRCh37") is False


@pytest.mark.parametrize("name", [None, "GRCh37"])
def test_check_if_assembly_exists(Session, tmp_path, setup, name):
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606, name) is False


@pytest.mark.parametrize("name", ["GRCh38", "GRCh37"])
def test_check_if_assembly_exists_empty_directory(Session, tmp_path, setup, name):
    service = _get_file_service(Session, tmp_path)
    service._get_assembly_dir(9606, name).mkdir(parents=True)
    assert service.check_if_assembly_exists(9606, name) is False


def test_check_if_assembly_exists_fail_no_chrom(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    service.create_chain_file(9606, "GRCh38")
    with pytest.raises(FileExistsError) as exc:
        service.check_if_assembly_exists(9606)
    assert str(exc.value) == "Files exist for assembly 'GRCh38'."


def test_check_if_assembly_exists_fail_with_chrom(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    service.create_assembly_file(9606, AssemblyFileType.INFO)
    service.create_assembly_file(9606, AssemblyFileType.RELEASE)
    with service.create_assembly_file(9606, AssemblyFileType.CHROM) as fh:
        fh.write("1\t248956422\n")
    with pytest.raises(FileExistsError) as exc:
        service.check_if_assembly_exists(9606)
    assert str(exc.value) == "Files exist for assembly 'GRCh38'."


#  Files


def test_upload(Session, tmp_path):
    stream = BytesIO(b"Some bedrmod data")
    service = _get_file_service(Session, tmp_path)
    file_id = service.upload_tmp_file(stream, 1024)
    assert service.check_tmp_upload_file_id(file_id) is True
    with service.open_tmp_upload_file_by_id(file_id) as fh:
        assert fh.read() == "Some bedrmod data"


# BAM


def test_create_bam_file(Session, tmp_path, dataset):
    dataset2 = dataset[1]
    stream = BytesIO(b"\x53\x6F\x6D\x65\x20\x62\x61\x6D\x20\x64\x61\x74\x61")

    service = _get_file_service(Session, tmp_path)
    service.create_or_update_bam_file(dataset2, "test.bam", stream, 1024)

    bam_list = service.get_bam_file_list(dataset2)
    assert len(bam_list) == 1
    assert bam_list[0]["original_file_name"] == "test.bam"
    assert bam_list[0]["size_in_bytes"] == 13

    bam = service.get_bam_file(dataset2, "test.bam")
    with service.open_bam_file(bam) as fh:
        assert fh.read() == b"Some bam data"
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(BamFile)) == 1

    service.remove_bam_file(bam)
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(BamFile)) == 0


def test_update_bam_file(Session, tmp_path, dataset, bam_file):
    dataset2 = dataset[1]
    stream = BytesIO(b"\x53\x6F\x6D\x65\x20\x62\x61\x6D\x20\x64\x61\x74\x61")
    service = _get_file_service(Session, tmp_path)
    service.create_or_update_bam_file(dataset2, "dataset_id02.bam", stream, 1024)
    bam = service.get_bam_file(dataset2, "dataset_id02.bam")
    with service.open_bam_file(bam) as fh:
        assert fh.read() == b"Some bam data"
    with Session() as session:
        assert session.scalar(select(func.count()).select_from(BamFile)) == 3


# vars


def test_count_lines(Session, tmp_path):
    test_file = Path(tmp_path, "example.txt")
    test_file.write_text("line1\nline2\nline3\n")
    service = _get_file_service(Session, tmp_path)
    assert service.count_lines(test_file) == 3
