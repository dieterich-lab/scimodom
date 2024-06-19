from pathlib import Path

import pytest
import requests  # type: ignore
from sqlalchemy import exists

from mocks.web_service import MockWebService, MockHTTPError
from scimodom.database.models import Assembly, AssemblyVersion, Taxonomy, Taxa
from scimodom.services.assembly import (
    AssemblyService,
    AssemblyNotFoundError,
    AssemblyVersionError,
    LiftOverError,
)
from scimodom.utils.specifications import ENSEMBL_FTP, ENSEMBL_ASM_MAPPING


class MockExternalService:
    def __init__(self):  # noqa
        pass

    def get_crossmap_output(self, raw_file, chain_file, unmapped=None, chrom_id="s"):
        return "lifted.bed", unmapped


@pytest.fixture
def chrom_file(data_path):
    d = data_path.ASSEMBLY_PATH / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)
    p = d / AssemblyService.CHROM_FILE
    p.write_text("1\t12345\n2\t123456", encoding="utf-8")


@pytest.fixture
def chain_file(data_path):
    d = data_path.ASSEMBLY_PATH / "Homo_sapiens" / "GRCh37"
    d.mkdir(parents=True, exist_ok=True)
    p = d / AssemblyService.CHAIN_FILE(source="GRCh37", target="GRCh38")
    p.touch()


def _get_assembly_service(Session, url_to_result=None, download_urls=None):
    return AssemblyService(
        session=Session(),
        external_service=MockExternalService(),  # noqa
        web_service=MockWebService(
            url_to_result=url_to_result, download_urls=download_urls
        ),  # noqa
    )


# tests


def test_assembly_path(data_path):
    assert AssemblyService.get_assembly_path() == data_path.ASSEMBLY_PATH


def test_init(Session, data_path):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session)
    assert service._version == "GcatSmFcytpU"


def test_get_organism(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assert service._get_organism(10090) == "Mus_musculus"


def test_get_chrom_file(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    expected_chrom_file = Path(
        data_path.ASSEMBLY_PATH, "Homo_sapiens", "GRCh38", service.CHROM_FILE
    )
    assert service.get_chrom_file(9606) == expected_chrom_file


def test_get_chain_file(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    pattern = service.CHAIN_FILE(source="GRCh37", target="GRCh38")
    expected_chain_file = Path(
        data_path.ASSEMBLY_PATH, "Homo_sapiens", "GRCh37", pattern
    )
    assert service.get_chain_file(9606, "GRCh37") == expected_chain_file


def test_get_assembly(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assembly = service.get_assembly_by_id(3)
    assert assembly.name == "GRCh37"
    assert assembly.alt_name == "hg19"
    assert assembly.taxa_id == 9606
    assert assembly.version == "J9dit7Tfc6Sb"
    assert service._version == "GcatSmFcytpU"


def test_get_assembly_fail(Session, data_path):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session)
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.get_assembly_by_id(99)
    assert (str(exc.value)) == "No such assembly with ID: 99."
    assert exc.type == AssemblyNotFoundError


@pytest.mark.parametrize("assembly_id,is_latest", [(1, True), (3, False)])
def test_is_latest_assembly(assembly_id, is_latest, Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assembly = service.get_assembly_by_id(assembly_id)
    assert service.is_latest_assembly(assembly) == is_latest


def test_get_seqids(Session, setup, chrom_file):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    seqids = service.get_seqids(9606)
    assert set(seqids) == {"1", "2"}


def test_liftover(Session, data_path, tmp_path, setup, chain_file):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assembly = service.get_assembly_by_id(3)

    d = tmp_path / "liftover"
    d.mkdir()
    # create raw_file
    raw_file = d / "raw_file.bed"
    raw_file.write_text(
        "1\t12345\t12346\tm6A\t1000\t+\t12345\t12346\t0,0,0\t10\t1\n", encoding="utf-8"
    )
    # create unmapped
    unmapped = d / "unmapped.bed"
    unmapped.touch()
    service.liftover(assembly, raw_file, unmapped_file=unmapped)


# with 3 raw_file records, liftover succeeds with the following warning:
# 1 records could not be mapped and were discarded... Contact the system administrator if you have questions.
def test_liftover_fail_count(Session, data_path, tmp_path, setup, chain_file):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assembly = service.get_assembly_by_id(3)

    d = tmp_path / "liftover"
    d.mkdir()
    # create raw_file
    raw_file = d / "raw_file.bed"
    content = """
    1\t12345\t12346\tm6A\t1000\t+\t12345\t12346\t0,0,0\t10\t1
    1\t12345\t12346\tm6A\t1000\t+\t12345\t12346\t0,0,0\t10\t1
    """
    raw_file.write_text(content, encoding="utf-8")
    # create unmapped
    unmapped = d / "unmapped.bed"
    unmapped.write_text(
        "1\t12345\t12346\tm6A\t1000\t+\t12345\t12346\t0,0,0\t10\t1\n", encoding="utf-8"
    )
    with pytest.raises(LiftOverError) as exc:
        service.liftover(assembly, raw_file, unmapped_file=unmapped)
    assert (str(exc.value)) == "Liftover failed: 1 records of 3 could not be mapped."
    assert exc.type == LiftOverError


def test_liftover_fail_version(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assembly = service.get_assembly_by_id(1)
    with pytest.raises(AssemblyVersionError) as exc:
        service.liftover(assembly, "raw_file")
    assert (str(exc.value)) == "Cannot liftover for latest assembly."
    assert exc.type == AssemblyVersionError


# downloads chain file...
def test_add_assembly(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(
        Session,
        download_urls=[
            "https://ftp.ensembl.org/pub/current_assembly_chain/homo_sapiens/NCBI36_to_GRCh38.chain.gz"
        ],
    )
    assembly_id = service.add_assembly(9606, "NCBI36")
    chain_file = service.get_chain_file(9606, "NCBI36")
    # asseemb;y_id is 4
    with Session() as session:
        assert session.query(
            exists().where(Assembly.taxa_id == 9606, Assembly.name == "NCBI36")
        ).scalar()
    assert service._web_service.files_created == [str(chain_file)]  # noqa


def test_add_assembly_exists(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    assert service.add_assembly(9606, "GRCh37") is None
    # normally directory exists for an existing assembly, but
    # this function does not check that, it simple returns if
    # the assembly exists
    # if the tests were fully isolated, this should be False...
    # chain_file = service.get_chain_file(9606, "GRCh37")
    # assert chain_file.parent.exists() is False


def test_add_assembly_file_exists(Session, chain_file):
    with Session() as session, session.begin():
        version = AssemblyVersion(version_num="GcatSmFcytpU")
        taxonomy = Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        )
        taxa = Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        )
        assembly = Assembly(
            name="GRCh38", alt_name="hg38", taxa_id=9606, version="GcatSmFcytpU"
        )
        session.add_all([version, taxonomy, taxa, assembly])
    service = _get_assembly_service(Session)
    with pytest.raises(FileExistsError) as exc:
        service.add_assembly(9606, "GRCh37")
    assert (
        (str(exc.value))
        == "[Errno 17] File exists: '/tmp/pytest-of-scimodom/data0/assembly/Homo_sapiens/GRCh37'"
    )


def test_add_assembly_wrong_url(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    with pytest.raises(MockHTTPError):
        service.add_assembly(9606, "GRCH37")


# this now fails because Assembly directory exists: /tmp/pytest-of-scimodom/data0/assembly/Homo_sapiens/GRCh38.
def test_prepare_assembly_for_version(Session, setup, data_path):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session)
    service.prepare_assembly_for_version(1)
    chrom_file = service.get_chrom_file(9606)
    assert chrom_file.is_file()
    assert Path(chrom_file.parent, "info.json").is_file()
    assert Path(chrom_file.parent, "release.json").is_file()


# the above with 2, adn 10090
# scimodom.services.assembly.AssemblyVersionError: Mismatch between assembly GRCm38 and coord system version GRCm39. Upgrade your database!
