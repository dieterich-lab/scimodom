import errno
import os
from io import BytesIO
from pathlib import Path

import pytest
from sqlalchemy import select, func

from scimodom.database.models import BamFile
from scimodom.services.file import (
    CacheNotAvailableException,
    CacheUpdateAlreadyRunning,
    FileService,
)
from scimodom.utils.specs.enums import (
    AssemblyFileType,
    IndexCacheType,
    TargetsFileType,
)


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


@pytest.fixture
def assembly_dir(tmp_path):
    # add empty assembly directory
    for name in ["GRCh37", "GRCh38"]:
        d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / name
        d.mkdir(parents=True, exist_ok=True)


@pytest.fixture
def assembly_files(tmp_path, assembly_dir):
    # add assembly files
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    for file_type in AssemblyFileType.common():
        Path(d, file_type.value).touch()
    with open(d / AssemblyFileType.CHROM.value, "w") as fh:
        fh.write("1\t248956422\n")
    for file_type in AssemblyFileType.fasta():
        Path(
            d,
            file_type.value(organism="Homo_sapiens", assembly="GRCh38", chrom=1),
        ).touch()
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh37"
    Path(
        d,
        AssemblyFileType.CHAIN.value(
            source_assembly="GRCh37", target_assembly="GRCh38"
        ),
    ).touch()


# tests


# Annotation


def test_get_annotation_dir(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_dir(9606) == Path(
        tmp_path, "t_data", "annotation", "Homo_sapiens", "GRCh38"
    )


def test_get_annotation_dir_explicit_assembly(Session, tmp_path, setup):
    # an explicit assembly name is used as given, and is not resolved
    # from the current assembly version
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_dir(9606, assembly_name="GRCh37") == Path(
        tmp_path, "t_data", "annotation", "Homo_sapiens", "GRCh37"
    )


def test_get_annotation_release_dir(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_release_dir(9606, "ensembl", 110) == Path(
        tmp_path, "t_data", "annotation", "Homo_sapiens", "GRCh38", "ensembl", "110"
    )


def test_get_annotation_release_dir_differs_by_source(Session, tmp_path, setup):
    # Annotation is unique on (release, taxa_id, source, version), so two
    # annotations differing only by source must not share a directory
    service = _get_file_service(Session, tmp_path)
    assert service.get_annotation_release_dir(
        9606, "ensembl", 110
    ) != service.get_annotation_release_dir(9606, "gtrnadb", 110)


def test_annotation_targets_file_is_not_below_release(Session, tmp_path, setup):
    # miRNA and RBP files belong to the assembly, not to an annotation
    # release: they stay directly below the annotation directory, cf. #146
    service = _get_file_service(Session, tmp_path)
    annotation_dir = service.get_annotation_dir(9606)
    annotation_dir.mkdir(parents=True, exist_ok=True)
    Path(annotation_dir, TargetsFileType.MIRNA.value()).write_text("mirna\n")
    with service.open_annotation_targets_file(
        9606, TargetsFileType.MIRNA, chrom="1"
    ) as fh:
        assert fh.read() == "mirna\n"


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


def test_gene_cache_permissions(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    gene_dir = tmp_path / "t_data" / FileService.GENE_CACHE_DEST
    old_umask = os.umask(0o077)  # the umask of the process is not used
    try:
        service.update_gene_cache(122, ["1"])
        service.update_gene_cache(122, ["2"])
    finally:
        os.umask(old_umask)
    assert (gene_dir / "122").stat().st_mode & 0o777 == 0o660
    assert [p.name for p in gene_dir.iterdir()] == ["122"]


def test_index_cache(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)

    def update_cache():
        def generator():
            yield "cache content"

        service.update_index_cache("chart", generator())

    service.run_index_update(IndexCacheType.SUNBURST, update_cache)
    with service.open_index_cache(IndexCacheType.SUNBURST, "chart") as fh:
        assert fh.read() == "cache content"
    path = tmp_path / "t_data" / FileService.INDEX_CACHE_DEST / "chart"
    # same as before (sunburst): for the owner only
    assert path.stat().st_mode & 0o777 == 0o600


def test_index_cache_not_available(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(CacheNotAvailableException) as exc_info:
        service.open_index_cache(IndexCacheType.AGGREGATES, "any_name.json")
    assert exc_info.value.cache == IndexCacheType.AGGREGATES
    service.update_index_cache("any_name.json", ["cache ", "content"])
    with service.open_index_cache(IndexCacheType.AGGREGATES, "any_name.json") as fh:
        assert fh.read() == "cache content"


@pytest.mark.parametrize("kind", ["gene", "index"])
def test_cache_update_is_atomic(Session, tmp_path, kind):
    service = _get_file_service(Session, tmp_path)

    def update(content):
        if kind == "gene":
            service.update_gene_cache(1, content)
        else:
            service.update_index_cache("name", content)

    def read():
        if kind == "gene":
            return service.get_gene_cache(1)
        with service.open_index_cache(IndexCacheType.SUNBURST, "name") as fh:
            return fh.read()

    update(["old"])
    path = (
        tmp_path
        / "t_data"
        / (
            FileService.GENE_CACHE_DEST / "1"
            if kind == "gene"
            else FileService.INDEX_CACHE_DEST / "name"
        )
    )
    with open(path) as reader:
        # a reader gets the old file, also while and after it is replaced
        update(["new"])
        assert reader.read().strip() == "old"
    assert read() in ("new", ["new"])


@pytest.mark.parametrize("kind", ["gene", "index"])
def test_cache_update_failure_is_raised_and_keeps_cache(Session, tmp_path, kind):
    service = _get_file_service(Session, tmp_path)

    def generator():
        yield "partial"
        raise OSError("disk full")

    if kind == "gene":
        cache_dir = tmp_path / "t_data" / FileService.GENE_CACHE_DEST
        name = "1"
        service.update_gene_cache(1, ["old"])
        with pytest.raises(OSError):
            service.update_gene_cache(1, generator())
    else:
        cache_dir = tmp_path / "t_data" / FileService.INDEX_CACHE_DEST
        name = "name"
        service.update_index_cache("name", ["old"])
        with pytest.raises(OSError):
            service.update_index_cache("name", generator())
    # the previous content is kept, no temporary file is left behind
    assert [p.name for p in cache_dir.iterdir()] == [name]
    assert (cache_dir / name).read_text().strip() == "old"


def test_cache_update_runs_again_if_requested_while_running(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)
    marker = (
        tmp_path / "t_data" / FileService.INDEX_CACHE_DEST / "aggregates.update_marker"
    )
    runs = []

    def update_cache():
        runs.append(1)
        if len(runs) == 1:
            # a request comes in while the update is running (cf. next test):
            # it is coalesced, the running update will run once more
            marker.touch()

    service.run_index_update(IndexCacheType.AGGREGATES, update_cache)
    assert len(runs) == 2
    assert marker.exists() is False


@pytest.mark.parametrize("code", [errno.EACCES, errno.EAGAIN])
def test_cache_update_already_running(mocker, Session, tmp_path, code):
    service = _get_file_service(Session, tmp_path)
    marker = (
        tmp_path / "t_data" / FileService.INDEX_CACHE_DEST / "aggregates.update_marker"
    )
    # another process holds the lock
    mocker.patch("scimodom.services.file.lockf", side_effect=OSError(code, "locked"))
    update_cache = mocker.Mock()
    with pytest.raises(CacheUpdateAlreadyRunning):
        service.run_index_update(IndexCacheType.AGGREGATES, update_cache)
    update_cache.assert_not_called()
    # the running update will see the request
    assert marker.exists() is True


def test_cache_update_other_lock_errors_are_not_already_running(
    mocker, Session, tmp_path
):
    service = _get_file_service(Session, tmp_path)
    mocker.patch(
        "scimodom.services.file.lockf", side_effect=OSError(errno.ENOLCK, "no locks")
    )
    update_cache = mocker.Mock()
    with pytest.raises(OSError) as exc_info:
        service.run_index_update(IndexCacheType.AGGREGATES, update_cache)
    assert not isinstance(exc_info.value, CacheUpdateAlreadyRunning)
    update_cache.assert_not_called()


def test_cache_update_failure_is_raised(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)

    def update_cache():
        raise ValueError("failed")

    with pytest.raises(ValueError):
        service.run_index_update(IndexCacheType.AGGREGATES, update_cache)
    # not locked anymore
    service.run_index_update(IndexCacheType.AGGREGATES, lambda: None)


def test_index_updates_are_independent(Session, tmp_path):
    service = _get_file_service(Session, tmp_path)

    def update_sunburst():
        # a different cache can be updated at the same time
        service.run_index_update(IndexCacheType.AGGREGATES, lambda: None)

    service.run_index_update(IndexCacheType.SUNBURST, update_sunburst)


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
    assert (str(exc.value)) == "Missing required parameter 'assembly_name'."


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
    assert (str(exc.value)) == "Missing required parameter 'chrom'."


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


def test_create_dna_sequence_file(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    with service.create_dna_sequence_file(9606, "1") as fh:
        fh.write(b"bla")
    path = Path(
        tmp_path,
        "t_data",
        "assembly",
        "Homo_sapiens",
        "GRCh38",
        AssemblyFileType.DNA.value(
            organism="Homo_sapiens", assembly="GRCh38", chrom="1"
        ),
    )
    with open(path, "rb") as fh:
        assert fh.read() == b"bla"


def test_create_dna_sequence_file_fail(Session, tmp_path, setup):
    service = _get_file_service(Session, tmp_path)
    try:
        with service.create_dna_sequence_file(9606, "1") as fh:
            fh.write(b"bla")
            raise Exception
    except Exception:
        pass

    path = Path(
        tmp_path,
        "t_data",
        "assembly",
        "Homo_sapiens",
        "GRCh38",
        AssemblyFileType.DNA.value(
            organism="Homo_sapiens", assembly="GRCh38", chrom="1"
        ),
    )
    assert path.exists() is False


@pytest.mark.parametrize("name", ["GRCh38", "GRCh37"])
def test_delete_assembly_and_check_if_exists(
    Session, tmp_path, setup, assembly_files, name
):
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606, name) is True
    service.delete_assembly(9606, name)
    assert service.check_if_assembly_exists(9606, name) is False
    # the other assembly should remain untouched
    names = ["GRCh37", "GRCh38"]
    if names.index(name) == 0:
        other_name = names[1]
    else:
        other_name = names[0]
    assert service.check_if_assembly_exists(9606, other_name) is True


@pytest.mark.parametrize("name", [None, "GRCh37"])
def test_check_if_assembly_exists(Session, tmp_path, setup, name):
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606, name) is False


@pytest.mark.parametrize("name", ["GRCh38", "GRCh37"])
def test_check_if_assembly_exists_empty_directory(
    Session, tmp_path, setup, assembly_dir, name
):
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606, name) is False


def test_check_if_assembly_exists_fail_no_chrom(
    Session, tmp_path, setup, assembly_files
):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    Path(d / AssemblyFileType.CHROM.value).unlink()
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(FileExistsError) as exc:
        service.check_if_assembly_exists(9606)
    assert str(exc.value) == "Files exist for assembly 'GRCh38'."


def test_check_if_assembly_exists_fail_with_chrom(
    Session, tmp_path, setup, assembly_files
):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    Path(
        d
        / AssemblyFileType.DNA.value(
            organism="Homo_sapiens", assembly="GRCh38", chrom=1
        ),
    ).unlink()
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(FileExistsError) as exc:
        service.check_if_assembly_exists(9606)
    assert str(exc.value) == "Files exist for assembly 'GRCh38'."


def test_check_if_assembly_exists_current_by_name(
    Session, tmp_path, setup, assembly_files
):
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606, "GRCh38") is True


def test_check_if_assembly_exists_blank_chrom_line(
    Session, tmp_path, setup, assembly_files
):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    with open(d / AssemblyFileType.CHROM.value, "a") as fh:
        fh.write("\n\n")
    service = _get_file_service(Session, tmp_path)
    assert service.check_if_assembly_exists(9606) is True


def test_check_if_assembly_exists_reports_missing_files(
    Session, tmp_path, setup, assembly_files
):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    Path(d / AssemblyFileType.INFO.value).unlink()
    service = _get_file_service(Session, tmp_path)
    with pytest.raises(FileExistsError) as exc:
        service.check_if_assembly_exists(9606)
    assert any(AssemblyFileType.INFO.value in n for n in exc.value.__notes__)


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
    stream = BytesIO(b"\x53\x6f\x6d\x65\x20\x62\x61\x6d\x20\x64\x61\x74\x61")

    service = _get_file_service(Session, tmp_path)
    service.create_or_update_bam_file(dataset2, "test.bam", stream, 1024)

    bam_list = service.get_bam_info_list(dataset2)
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


def _create_bam(Session, tmp_path, dataset):
    service = _get_file_service(Session, tmp_path)
    service.create_or_update_bam_file(
        dataset, "test.bam", BytesIO(b"Some bam data"), 1024
    )
    bam = service.get_bam_file(dataset, "test.bam")
    return service, bam, Path(service._get_bam_file_path(bam))


def test_remove_bam_file_deletes_file(Session, tmp_path, dataset, bam_file):
    service, bam, path = _create_bam(Session, tmp_path, dataset[1])
    assert path.is_file()
    service.remove_bam_file(bam)
    assert not path.exists()


def test_remove_bam_file_keeps_file_if_commit_fails(
    Session, tmp_path, dataset, bam_file, mocker
):
    service, bam, path = _create_bam(Session, tmp_path, dataset[1])
    mocker.patch.object(service._session, "commit", side_effect=RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        service.remove_bam_file(bam)
    # the record still exists, and must still have its file
    assert path.is_file()
    with Session() as session:
        assert session.scalar(
            select(func.count()).select_from(BamFile).filter_by(id=bam.id)
        )


def test_delete_bam_file_records_does_not_commit(Session, tmp_path, dataset, bam_file):
    service, bam, path = _create_bam(Session, tmp_path, dataset[1])

    def count(dataset_id=None):
        query = select(func.count()).select_from(BamFile)
        if dataset_id is not None:
            query = query.filter_by(dataset_id=dataset_id)
        return service._session.scalar(query)

    total = count()
    paths = service.delete_bam_file_records(dataset[1])
    # all BAM files of this dataset, nothing else, and the files are untouched
    assert path in paths
    assert len(paths) == 2
    assert all(isinstance(p, Path) for p in paths)
    assert path.is_file()
    # not committed: rolling back restores the records
    service._session.rollback()
    assert count() == total


def test_remove_files(tmp_path, caplog):
    existing = tmp_path / "exists.bam"
    existing.write_text("data")
    directory = tmp_path / "directory"  # cannot be unlinked
    directory.mkdir()
    FileService.remove_files([tmp_path / "missing.bam", directory, existing])
    # never raises, a missing file is fine, others are logged, and the rest is done
    assert not existing.exists()
    assert directory.is_dir()
    assert f"Failed to delete '{directory}'" in caplog.text
    assert "missing.bam" not in caplog.text


def test_update_bam_file(Session, tmp_path, dataset, bam_file):
    dataset2 = dataset[1]
    stream = BytesIO(b"\x53\x6f\x6d\x65\x20\x62\x61\x6d\x20\x64\x61\x74\x61")
    service = _get_file_service(Session, tmp_path)
    service.create_or_update_bam_file(dataset2, "dataset00002.bam", stream, 1024)
    bam = service.get_bam_file(dataset2, "dataset00002.bam")
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
