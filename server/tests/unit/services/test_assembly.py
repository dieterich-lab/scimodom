from pathlib import Path

import pytest

from scimodom.services.assembly import AssemblyService, AssemblyVersionError


def test_init_from_id_wrong_version(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    # excinfo.value contains msg
    with pytest.raises(AssemblyVersionError) as excinfo:
        service = AssemblyService.from_id(Session(), assembly_id=3)


def test_init_from_id(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AssemblyService.from_id(Session(), assembly_id=1)
    assert service._name == "GRCh38"
    assert service._taxid == 9606
    organism = service._get_organism()
    assert service._chrom_file == Path(
        data_path.ASSEMBLY_PATH, organism, service._name, "chrom.sizes"
    )


def test_init_from_new_exists(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = AssemblyService.from_new(Session(), name="GRCh38", taxa_id=9606)
    assert service._assembly_id == 1
    organism = service._get_organism()
    assert service._chrom_file == Path(
        data_path.ASSEMBLY_PATH, organism, "GRCh38", "chrom.sizes"
    )


@pytest.mark.parametrize(
    "name,taxid",
    [
        ("GRCh38", None),
        (None, 9606),
        ("GRCh38", 0000),
    ],
)
def test_init_from_new_fail(name, taxid, Session, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    error = TypeError
    if taxid == 0000:
        error = ValueError
    with pytest.raises(error) as excinfo:
        service = AssemblyService.from_new(Session(), name=name, taxa_id=taxid)


def test_init_from_new(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = AssemblyService.from_new(Session(), name="NCBI36", taxa_id=9606)
    parent, filen = service.get_chain_path()
    chain_file = Path(parent, filen)
    # check if file exists, not content
    assert chain_file.is_file()


def test_create_new(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = AssemblyService.from_id(Session(), assembly_id=1)
    service.create_new()
    organism = service._get_organism()
    assembly = service._name
    parent, _ = service.get_chrom_path(data_path.ASSEMBLY_PATH, organism, assembly)
    # check if files exist, not content
    assert service._chrom_file.is_file()
    assert Path(parent, "info.json").is_file()
    assert Path(parent, "release.json").is_file()


def test_create_new_fail(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    with pytest.raises(AssemblyVersionError) as excinfo:
        service = AssemblyService.from_new(Session(), name="GRCh37", taxa_id=9606)
        service.create_new()


def test_create_new_exists(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = AssemblyService.from_id(Session(), assembly_id=1)
    organism = service._get_organism()
    assembly = service._name
    parent, _ = service.get_chrom_path(data_path.ASSEMBLY_PATH, organism, assembly)
    parent.mkdir(parents=True, exist_ok=True)
    with pytest.raises(Exception) as excinfo:
        service.create_new()
