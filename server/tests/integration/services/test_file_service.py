from os.path import join
from pathlib import Path

import pytest
from sqlalchemy import select

from scimodom.database.models import AssemblyVersion, Assembly, Taxa, Taxonomy, Organism
from scimodom.services.file import FileService, AssemblyFileType


def get_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=join(tmp_path, "t_data"),
        temp_path=join(tmp_path, "t_temp"),
        upload_path=join(tmp_path, "t_upload"),
        import_path=join(tmp_path, "t_import"),
    )


@pytest.fixture
def assembly(Session):
    with Session() as db:
        db.add_all(
            [
                AssemblyVersion(version_num="v23"),
                Taxonomy(id="tax", domain="domain", kingdom="kingdom", phylum="phylum"),
                Taxa(
                    id=15, name="The Wrong One", short_name="wrong", taxonomy_id="tax"
                ),
                Taxa(
                    id=16, name="The Right Taxa", short_name="right", taxonomy_id="tax"
                ),
                Assembly(id=1, name="asWrongTaxa", taxa_id=15, version="v23"),
                Assembly(id=2, name="asWrongVersion", taxa_id=16, version="v22"),
                Assembly(id=3, name="asRight", taxa_id=16, version="v23"),
            ]
        )
        db.commit()


def test_assembly_path(Session, tmp_path, assembly):
    service = get_service(Session, tmp_path)
    assert service.get_assembly_file_path(16, AssemblyFileType.CHROM) == Path(
        tmp_path, "t_data", "assembly", "The_right_taxa", "asRight", "chrom.sizes"
    )


def test_create_chain_file(Session, tmp_path, assembly):
    service = get_service(Session, tmp_path)
    with service.create_chain_file(16, "x_to_y.chain") as fh:
        fh.write(b"bla")
    path = Path(
        tmp_path, "t_data", "assembly", "The_right_taxa", "asRight", "x_to_y.chain"
    )
    with open(path, "rb") as fh:
        assert fh.read() == b"bla"


def test_count_lines(Session, tmp_path):
    test_file = Path(tmp_path, "example.txt")
    test_file.write_text("line1\nline2\nline3\n")
    service = get_service(Session, tmp_path)
    assert service.count_lines(test_file) == 3


def test_get_annotation_path(Session, tmp_path):
    service = get_service(Session, tmp_path)
    assert service.get_annotation_dir() == Path(tmp_path, "t_data", "annotation")


def test_gene_cache(Session, tmp_path):
    service = get_service(Session, tmp_path)
    service.update_gene_cache(122, ["1", "2", "Y"])
    service.update_gene_cache(123, ["1", "3"])
    service.update_gene_cache(124, ["1", "3", "X"])
    assert service.get_gene_cache([122, 123]) == {"1", "2", "3", "Y"}
    service.update_gene_cache(123, ["1", "15"])
    assert service.get_gene_cache([122, 123]) == {"1", "2", "15", "Y"}
