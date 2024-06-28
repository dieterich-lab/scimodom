from abc import ABC
from io import StringIO, BytesIO
from pathlib import Path
from typing import TextIO, BinaryIO

import pytest
import requests  # type: ignore
from sqlalchemy import exists

from mocks.io_mocks import MockStringIO, MockBytesIO
from mocks.web_service import MockWebService, MockHTTPError
from scimodom.database.models import Assembly, AssemblyVersion, Taxonomy, Taxa
from scimodom.services.assembly import (
    AssemblyService,
    AssemblyNotFoundError,
    AssemblyVersionError,
    LiftOverError,
)
from scimodom.services.file import AssemblyFileType


class MockExternalService:
    def get_crossmap_output(self, raw_file, chain_file, unmapped=None, chrom_id="s"):
        return "lifted.bed", unmapped


class MockFileService:
    def __init__(self):
        self.files_by_name: dict[str, MockStringIO | MockBytesIO] = {}
        self.lines_by_name: dict[str, int] = {}
        self.existing_assemblies: list[int] = []
        self.deleted_assemblies: list[int] = []

    @staticmethod
    def get_assembly_file_path(
        taxa_id: int, file_type: AssemblyFileType, chain_file_name: str | None = None
    ) -> Path:
        if file_type == AssemblyFileType.CHAIN:
            return Path(f"/data/assembly/{taxa_id}/{chain_file_name}")
        else:
            return Path(f"/data/assembly/{taxa_id}/{file_type.value}")

    def open_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        if file_type == AssemblyFileType.CHAIN:
            raise NotImplementedError()
        name = self.get_assembly_file_path(taxa_id, file_type).as_posix()
        file = self.files_by_name[name]
        file.seek(0)
        return file

    def create_assembly_file(self, taxa_id: int, file_type: AssemblyFileType) -> TextIO:
        if file_type == AssemblyFileType.CHAIN:
            raise NotImplementedError()
        name = self.get_assembly_file_path(taxa_id, file_type).as_posix()
        new_file = MockStringIO()
        self.files_by_name[name] = new_file
        return new_file

    def create_chain_file(self, taxa_id: int, name: str) -> BinaryIO:
        name = self.get_assembly_file_path(
            taxa_id, AssemblyFileType.CHAIN, chain_file_name=name
        ).as_posix()
        new_file = MockBytesIO()
        self.files_by_name[name] = new_file
        return new_file

    def check_if_assembly_exists(self, taxa_id: int) -> bool:
        return taxa_id in self.existing_assemblies

    def delete_assembly(self, taxa_id: int):
        self.deleted_assemblies.append(taxa_id)

    def count_lines(self, path):
        return self.lines_by_name[path]


@pytest.fixture
def file_service():
    yield MockFileService()


@pytest.fixture
def chain_file(file_service):
    file_service.files_by_name["/data/assembly/9606/GRCh37_to_GRCh38.chain"] = BytesIO()


def _get_assembly_service(Session, file_service, url_to_result=None, url_to_data=None):
    return AssemblyService(
        session=Session(),
        external_service=MockExternalService(),  # noqa
        web_service=MockWebService(
            url_to_result=url_to_result, url_to_data=url_to_data
        ),  # noqa
        file_service=file_service,  # noqa
    )


# tests


def test_init(Session, data_path, file_service):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session, file_service)
    assert service._version == "GcatSmFcytpU"


def test_get_organism(Session, file_service, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    assert (
        service._get_organism(10090) == "Mus musculus"
    )  # Converting space to '_' is now done in file service.


def test_get_assembly(Session, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    assert assembly.name == "GRCh37"
    assert assembly.alt_name == "hg19"
    assert assembly.taxa_id == 9606
    assert assembly.version == "J9dit7Tfc6Sb"
    assert service._version == "GcatSmFcytpU"


def test_get_assembly_fail(Session, data_path):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.get_assembly_by_id(99)
    assert (str(exc.value)) == "No such assembly with ID: 99."
    assert exc.type == AssemblyNotFoundError


@pytest.mark.parametrize("assembly_id,is_latest", [(1, True), (3, False)])
def test_is_latest_assembly(
    assembly_id, is_latest, Session, file_service, data_path, setup
):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(assembly_id)
    assert service.is_latest_assembly(assembly) == is_latest


def test_get_seqids(Session, file_service, setup):
    file_service.files_by_name["/data/assembly/9606/chrom.sizes"] = StringIO(
        "1\t12345\n2\t123456"
    )
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    seqids = service.get_seqids(9606)
    assert set(seqids) == {"1", "2"}


def test_liftover(Session, file_service, setup, chain_file):
    with Session() as session, session.begin():
        session.add_all(setup)
    file_service.lines_by_name["unmapped.bed"] = 0
    file_service.lines_by_name["to_be_lifted.bed"] = 3
    file_service.lines_by_name["lifted.bed"] = 3
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    service.liftover(assembly, "to_be_lifted.bed", unmapped_file="unmapped.bed")


# with 3 raw_file records, liftover succeeds with the following warning:
# 1 records could not be mapped and were discarded... Contact the system administrator if you have questions.
def test_liftover_fail_count(Session, file_service, setup, chain_file):
    with Session() as session, session.begin():
        session.add_all(setup)
    file_service.lines_by_name["unmapped.bed"] = 1
    file_service.lines_by_name["to_be_lifted.bed"] = 3
    file_service.lines_by_name["lifted.bed"] = 2
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    with pytest.raises(LiftOverError) as exc:
        service.liftover(assembly, "to_be_lifted.bed", unmapped_file="unmapped.bed")
    assert (str(exc.value)) == "Liftover failed: 1 records of 3 could not be mapped."
    assert exc.type == LiftOverError


def test_liftover_fail_version(Session, file_service, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(1)
    with pytest.raises(AssemblyVersionError) as exc:
        service.liftover(assembly, "raw_file")
    assert (str(exc.value)) == "Cannot liftover for latest assembly."
    assert exc.type == AssemblyVersionError


# downloads chain file...
def test_add_assembly(Session, file_service, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(
        Session,
        file_service,
        url_to_data={
            "https://ftp.ensembl.org/pub/current_assembly_chain/homo_sapiens/NCBI36_to_GRCh38.chain.gz": b"foo"
        },
    )
    service.add_assembly(9606, "NCBI36")
    # asseemb;y_id is 4
    with Session() as session:
        assert session.query(
            exists().where(Assembly.taxa_id == 9606, Assembly.name == "NCBI36")
        ).scalar()
    file = file_service.files_by_name["/data/assembly/9606/NCBI36_to_GRCh38.chain.gz"]
    assert file.final_content == b"foo"


def test_add_assembly_exists(Session, file_service, data_path, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    assert service.add_assembly(9606, "GRCh37") == 3
    # normally directory exists for an existing assembly, but
    # this function does not check that, it simple returns if
    # the assembly exists
    # if the tests were fully isolated, this should be False...
    # chain_file = service.get_chain_file(9606, "GRCh37")
    # assert chain_file.parent.exists() is False
    #
    # HW: Check with Etienne - that is a true uni test now!
    #


def test_add_assembly_file_exists(Session, file_service):
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
    file_service.existing_assemblies = [9606]
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(FileExistsError) as exc:
        service.add_assembly(9606, "GRCh37")
    assert (str(exc.value)) == "Assembly 'GRCh37' already exists (Taxa ID 9606)."


def test_add_assembly_wrong_url(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(MockHTTPError):
        service.add_assembly(9606, "GRCH37")


EXAMPLE_GENE_BUILD_DATA = {
    "assembly_accession": "GCA_000001405.29",
    "assembly_date": "2013-12",
    "assembly_name": "GRCh38.p14",
    "coord_system_versions": ["GRCh38", "GRCh37"],
    "default_coord_system_version": "GRCh38",
    "karyotype": ["1", "2", "X"],
    "top_level_region": [
        {"coord_system": "chromosome", "length": 248956422, "name": "1"},
        {"coord_system": "chromosome", "length": 242193529, "name": "2"},
        {
            "coord_system": "chromosome",
            "length": 156040895,
            "name": "X",
        },
    ],
}

EXPECTED_CHROM_SIZES = """1\t248956422
2\t242193529
X\t156040895
"""

EXPECTED_INFO_JSON = """{
\t"assembly_accession": "GCA_000001405.29",
\t"assembly_date": "2013-12",
\t"assembly_name": "GRCh38.p14"
}"""

EXPECTED_RELEASE_JSON = """{
\t"releases": [
\t\t112
\t]
}"""


# this now fails because Assembly directory exists: /tmp/pytest-of-scimodom/data0/assembly/Homo_sapiens/GRCh38.
def test_prepare_assembly_for_version(Session, file_service, setup):
    with Session() as session, session.begin():
        session.add_all(setup)
    service = _get_assembly_service(
        Session,
        file_service,
        url_to_result={
            "http://rest.ensembl.org/info/assembly/homo_sapiens": EXAMPLE_GENE_BUILD_DATA,
            "http://rest.ensembl.org/info/data": {"releases": [112]},
        },
    )
    service.prepare_assembly_for_version(1)
    assert (
        file_service.files_by_name["/data/assembly/9606/chrom.sizes"].final_content
        == EXPECTED_CHROM_SIZES
    )
    assert (
        file_service.files_by_name["/data/assembly/9606/info.json"].final_content
        == EXPECTED_INFO_JSON
    )
    assert (
        file_service.files_by_name["/data/assembly/9606/release.json"].final_content
        == EXPECTED_RELEASE_JSON
    )


# the above with 2, adn 10090
# scimodom.services.assembly.AssemblyVersionError: Mismatch between assembly GRCm38 and coord system version GRCm39. Upgrade your database!
