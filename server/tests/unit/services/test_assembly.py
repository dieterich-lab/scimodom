from pathlib import Path

import pytest

from scimodom.services.assembly import AssemblyService, AssemblyVersionError

import os


def test_init_from_id_wrong_version(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(AssemblyVersionError) as exc:
        service = AssemblyService.from_id(Session(), assembly_id=3)
    assert (
        (str(exc.value))
        == "Mismatch between current DB assembly version (GcatSmFcytpU) and version (J9dit7Tfc6Sb) from assembly ID = 3. Aborting transaction!"
    )
    assert exc.type == AssemblyVersionError


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
    "name,taxid,error,msg",
    [
        (
            "GRCh38",
            None,
            ValueError,
            "Taxonomy ID = None not found! Aborting transaction!",
        ),
        (None, 9606, TypeError, "Expected str; got NoneType"),
        (
            "GRCh38",
            0000,
            ValueError,
            "Taxonomy ID = 0 not found! Aborting transaction!",
        ),
    ],
)
def test_init_from_new_fail(name, taxid, error, msg, Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    with pytest.raises(error) as exc:
        service = AssemblyService.from_new(Session(), name=name, taxa_id=taxid)
    assert str(exc.value) == msg
    assert exc.type == error


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
    parent, _ = service.get_chrom_path(organism, assembly)
    # check if files exist, not content
    assert service._chrom_file.is_file()
    assert Path(parent, "info.json").is_file()
    assert Path(parent, "release.json").is_file()


def test_create_new_fail(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    with pytest.raises(AssemblyVersionError) as exc:
        service = AssemblyService.from_new(Session(), name="GRCh37", taxa_id=9606)
        service.create_new()
    assert (
        (str(exc.value))
        == "Mismatch between current DB assembly version (GcatSmFcytpU) and version (J9dit7Tfc6Sb). Cannot call this function! Aborting transaction!"
    )
    assert exc.type == AssemblyVersionError


def test_create_new_exists(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)

    service = AssemblyService.from_id(Session(), assembly_id=1)
    organism = service._get_organism()
    assembly = service._name
    parent, _ = service.get_chrom_path(organism, assembly)
    parent.mkdir(parents=True, exist_ok=True)
    with pytest.raises(Exception) as exc:
        service.create_new()
    assert (
        str(exc.value)
        == f"Assembly directory at {parent} already exists... Aborting transaction!"
    )
