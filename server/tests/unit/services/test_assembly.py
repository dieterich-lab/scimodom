from io import StringIO, BytesIO
from pathlib import Path
from typing import TextIO, BinaryIO

import pytest
from sqlalchemy import exists

from scimodom.database.models import Assembly, AssemblyVersion
from scimodom.services.assembly import (
    AssemblyService,
    AssemblyNotFoundError,
    AssemblyVersionError,
    AssemblyAbortedError,
    LiftOverError,
)
from scimodom.utils.specs.enums import AssemblyFileType
from tests.mocks.enums import MockEnsembl
from tests.mocks.io import MockStringIO, MockBytesIO
from tests.mocks.web import MockWebService


class MockExternalService:
    def get_crossmap_output(
        self, raw_file, chain_file, unmapped=None, chrom_id="s"
    ):  # noqa
        return "lifted.bed", unmapped


class MockFileService:
    def __init__(self):
        self.files_by_name: dict[str, MockStringIO | MockBytesIO] = {}
        self.lines_by_name: dict[str, int] = {}
        self.existing_assemblies: list[tuple[int, str]] = []
        self.deleted_assemblies: list[tuple[int, str]] = []

    @staticmethod
    def open_file_for_reading(path: str) -> str:
        return path

    @staticmethod
    def get_assembly_file_path(
        taxa_id: int,
        file_type: AssemblyFileType,
        chain_file_name: str | None = None,
        chain_assembly_name: str | None = None,
    ) -> Path:
        if file_type == AssemblyFileType.CHAIN:
            return Path(
                f"/data/assembly/{taxa_id}/{chain_assembly_name}/{chain_file_name}"
            )
        else:
            return Path(f"/data/assembly/{taxa_id}/{file_type.value}")

    def open_assembly_file(
        self, taxa_id: int, file_type: AssemblyFileType
    ) -> MockStringIO | MockBytesIO:
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

    def create_chain_file(
        self, taxa_id: int, file_name: str, assembly_name: str
    ) -> BinaryIO:
        name = self.get_assembly_file_path(
            taxa_id,
            AssemblyFileType.CHAIN,
            chain_file_name=file_name,
            chain_assembly_name=assembly_name,
        ).as_posix()
        new_file = MockBytesIO()
        self.files_by_name[name] = new_file
        return new_file

    def check_if_assembly_exists(self, taxa_id: int, assembly_name: str) -> bool:
        return (taxa_id, assembly_name) in self.existing_assemblies

    def delete_assembly(self, taxa_id: int, assembly_name: str):
        self.deleted_assemblies.append((taxa_id, assembly_name))

    def count_lines(self, path):
        return self.lines_by_name[path]


@pytest.fixture
def file_service():
    yield MockFileService()


def _get_assembly_service(Session, file_service, url_to_result=None, url_to_data=None):
    return AssemblyService(
        session=Session(),
        external_service=MockExternalService(),
        web_service=MockWebService(
            url_to_result=url_to_result, url_to_data=url_to_data
        ),
        file_service=file_service,
    )


# tests


def test_init(Session, file_service):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session, file_service)
    assert service._version == "GcatSmFcytpU"


def test_get_assembly_by_id(Session, file_service, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    assert assembly.name == "GRCh37"
    assert assembly.alt_name == "hg19"
    assert assembly.taxa_id == 9606
    assert assembly.version == "J9dit7Tfc6Sb"
    assert service._version == "GcatSmFcytpU"


def test_get_assembly_by_id_fail(Session):
    with Session() as session, session.begin():
        session.add(AssemblyVersion(version_num="GcatSmFcytpU"))
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.get_assembly_by_id(99)
    assert (str(exc.value)) == "No such assembly with ID: 99."
    assert exc.type == AssemblyNotFoundError


def test_get_assemblies_by_taxa(Session, file_service, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    assemblies = service.get_assemblies_by_taxa(9606)

    expected_assemblies = [
        ("GRCh38", "GcatSmFcytpU"),
        ("GRCh37", "J9dit7Tfc6Sb"),
    ]
    for assembly, expected_assembly in zip(assemblies, expected_assemblies):
        assert assembly.name == expected_assembly[0]
        assert assembly.version == expected_assembly[1]


@pytest.mark.parametrize("assembly_id,is_latest", [(1, True), (3, False)])
def test_is_latest_assembly(
    assembly_id, is_latest, Session, file_service, setup
):  # noqa
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(assembly_id)
    assert service.is_latest_assembly(assembly) == is_latest


def test_get_name_for_version(Session, file_service, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    assembly_name = service.get_name_for_version(9606)
    assert assembly_name == "GRCh38"


def test_get_seqids(Session, file_service, setup):  # noqa
    file_service.files_by_name["/data/assembly/9606/chrom.sizes"] = StringIO(
        "1\t12345\n2\t123456"
    )
    service = _get_assembly_service(Session, file_service)
    seqids = service.get_seqids(9606)
    assert set(seqids) == {"1", "2"}


def test_get_chroms(Session, file_service, setup):  # noqa
    file_service.files_by_name["/data/assembly/9606/chrom.sizes"] = StringIO(
        "1\t12345\n2\t123456"
    )
    service = _get_assembly_service(Session, file_service)
    chroms = service.get_chroms(9606)
    expected_chroms = [{"chrom": "1", "size": 12345}, {"chrom": "2", "size": 123456}]
    for chrom, expected_chrom in zip(chroms, expected_chroms):
        assert chrom == expected_chrom


def test_liftover(Session, file_service, setup):  # noqa
    file_service.files_by_name[
        "/data/assembly/9606/GRCh37/GRCh37_to_GRCh38.chain.gz"
    ] = BytesIO()
    file_service.lines_by_name["unmapped.bed"] = 0
    file_service.lines_by_name["to_be_lifted.bed"] = 3
    file_service.lines_by_name["lifted.bed"] = 3
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    service.create_lifted_file(
        assembly, "to_be_lifted.bed", unmapped_file="unmapped.bed"
    )


def test_liftover_fail_count(Session, file_service, setup):  # noqa
    file_service.files_by_name[
        "/data/assembly/9606/GRCh37/GRCh37_to_GRCh38.chain.gz"
    ] = BytesIO()
    file_service.lines_by_name["unmapped.bed"] = 1
    file_service.lines_by_name["to_be_lifted.bed"] = 3
    file_service.lines_by_name["lifted.bed"] = 2
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    with pytest.raises(LiftOverError) as exc:
        service.create_lifted_file(
            assembly, "to_be_lifted.bed", unmapped_file="unmapped.bed"
        )
    assert (
        str(exc.value)
    ) == "Liftover failed: 1 records out of 3 could not be mapped."
    assert exc.type == LiftOverError


def test_liftover_warning(Session, file_service, setup, caplog):  # noqa
    file_service.files_by_name[
        "/data/assembly/9606/GRCh37/GRCh37_to_GRCh38.chain.gz"
    ] = BytesIO()
    file_service.lines_by_name["unmapped.bed"] = 1
    file_service.lines_by_name["to_be_lifted.bed"] = 4
    file_service.lines_by_name["lifted.bed"] = 3
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(3)
    service.create_lifted_file(
        assembly, "to_be_lifted.bed", unmapped_file="unmapped.bed"
    )
    assert caplog.messages == [
        "1 records could not be mapped... Contact the system administrator if you have questions."
    ]


def test_liftover_fail_version(Session, file_service, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    assembly = service.get_assembly_by_id(1)
    with pytest.raises(AssemblyVersionError) as exc:
        service.create_lifted_file(assembly, "raw_file")
    assert (str(exc.value)) == "Cannot liftover for latest assembly."
    assert exc.type == AssemblyVersionError


# test_add_assembly and test_prepare_assembly_for_version all implicitely
# test protected methods e.g. _handle_gene_build and _handle_release


INFO = """{
\t"assembly_accession": "GCA_000001405.29",
\t"assembly_date": "2013-12",
\t"assembly_name": "GRCh38.p14",
\t"coord_system_versions": [
\t\t"GRCh38",
\t\t"GRCh37",
\t\t"NCBI36",
\t\t"NCBI35",
\t\t"NCBI34"
\t]
}"""


def test_get_assembly_by_name(Session, file_service, setup, mocker):  # noqa
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    file_service.files_by_name["/data/assembly/9606/info.json"] = StringIO(INFO)
    service = _get_assembly_service(
        Session,
        file_service,
        url_to_data={
            "https://ftp.ensembl.org/pub/release-110/assembly_chain/homo_sapiens/NCBI36_to_GRCh38.chain.gz": b"foo"
        },
    )
    assembly = service.get_assembly_by_name(9606, "NCBI36")
    with Session() as session:
        assert session.query(
            exists().where(Assembly.taxa_id == 9606, Assembly.name == "NCBI36")
        ).scalar()
        assert assembly.id == 4
    file = file_service.files_by_name[
        "/data/assembly/9606/NCBI36/NCBI36_to_GRCh38.chain.gz"
    ]
    assert file.final_content == b"foo"


def test_get_assembly_by_name_exists(Session, file_service, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    assert service.get_assembly_by_name(9606, "GRCh37").id == 3


def test_get_assembly_by_name_directory_exists(Session, file_service):
    with Session() as session, session.begin():
        version = AssemblyVersion(version_num="GcatSmFcytpU")
        session.add(version)
    file_service.existing_assemblies = [(9606, "GRCh37")]
    # INFO is wrong for this assembly, but for testing this doesn't matter...
    file_service.files_by_name["/data/assembly/9606/info.json"] = StringIO(INFO)
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyAbortedError) as exc:
        service.get_assembly_by_name(9606, "GRCh37")
    assert (
        (str(exc.value))
        == "Suspected data corruption for 'GRCh37'. Files were found on the system, but assembly does not exist in the database."
    )


def test_get_assembly_by_name_wrong_name(Session, file_service, setup):  # noqa
    file_service.files_by_name["/data/assembly/9606/info.json"] = StringIO(INFO)
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.get_assembly_by_name(9606, "GRCH37")
    assert (
        (str(exc.value))
        == "No such assembly 'GRCH37' for organism '9606'. Valid assemblies are: 'GRCh38 GRCh37 NCBI36 NCBI35 NCBI34'"
    )
    with Session() as session:
        assert session.query(Assembly).count() == 3


def test_get_assembly_by_name_wrong_url(Session, file_service, setup, mocker):  # noqa
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    file_service.files_by_name["/data/assembly/9606/info.json"] = StringIO(INFO)
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyAbortedError) as exc:  # traceback MockHTTPError
        service.get_assembly_by_name(9606, "NCBI36")
    assert (str(exc.value)) == "Adding assembly for 'NCBI36' aborted."
    assert file_service.deleted_assemblies == [(9606, "NCBI36")]
    with Session() as session:
        assert session.query(Assembly).count() == 3


def test_get_assembly_by_name_not_found(Session, setup):  # noqa
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyNotFoundError) as exc:
        service.get_assembly_by_name(9606, "NCBI36", fail_safe=False)
    assert (str(exc.value)) == "No such assembly 'NCBI36' for organism '9606'."
    with Session() as session:
        assert session.query(Assembly).count() == 3


EXAMPLE_GENE_BUILD_DATA = {
    "assembly_accession": "GCA_000001405.29",
    "assembly_date": "2013-12",
    "assembly_name": "GRCh38.p14",
    "coord_system_versions": ["GRCh38", "GRCh37", "NCBI36", "NCBI35", "NCBI34"],
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


NEWEST_EXAMPLE_GENE_BUILD_DATA = EXAMPLE_GENE_BUILD_DATA.copy()
NEWEST_EXAMPLE_GENE_BUILD_DATA["default_coord_system_version"] = "GRCh39"


EXPECTED_CHROM_SIZES = """1\t248956422
2\t242193529
X\t156040895
"""

EXPECTED_INFO_JSON = INFO

EXPECTED_RELEASE_JSON = """{
\t"releases": [
\t\t110
\t]
}"""


def test_prepare_assembly_for_version(Session, file_service, setup, mocker):  # noqa
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    service = _get_assembly_service(
        Session,
        file_service,
        url_to_result={
            "http://jul2023.rest.ensembl.org/info/assembly/homo_sapiens": EXAMPLE_GENE_BUILD_DATA,
            "http://jul2023.rest.ensembl.org/info/data": {"releases": [110]},
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


def test_prepare_assembly_for_version_wrong_version(
    Session, file_service, setup
):  # noqa
    service = _get_assembly_service(
        Session,
        file_service,
    )
    with pytest.raises(AssemblyVersionError) as exc:
        service.prepare_assembly_for_version(3)
    assert (
        (str(exc.value))
        == "Mismatch between assembly version 'J9dit7Tfc6Sb' and database version 'GcatSmFcytpU'."
    )
    assert exc.type == AssemblyVersionError


def test_prepare_assembly_for_version_directory_exists(
    Session, file_service, setup
):  # noqa
    file_service.existing_assemblies = [(9606, "GRCh38")]
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(FileExistsError) as exc:
        service.prepare_assembly_for_version(1)
    assert (str(exc.value)) == "Assembly 'GRCh38' already exists (Taxa ID 9606)."


def test_prepare_assembly_for_version_build_error(Session, file_service, setup, mocker):
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    service = _get_assembly_service(
        Session,
        file_service,
        url_to_result={
            "http://jul2023.rest.ensembl.org/info/assembly/homo_sapiens": NEWEST_EXAMPLE_GENE_BUILD_DATA,
            "http://jul2023.rest.ensembl.org/info/data": {"releases": [112]},
        },
    )
    with pytest.raises(AssemblyVersionError) as exc:
        service.prepare_assembly_for_version(1)
    assert (
        str(exc.value)
    ) == "Mismatch between assembly GRCh38 and coord system version GRCh39."
    assert exc.type == AssemblyVersionError
    assert file_service.deleted_assemblies == [(9606, "GRCh38")]


def test_prepare_assembly_for_version_wrong_url(
    Session, file_service, setup, mocker
):  # noqa
    mocker.patch("scimodom.services.assembly.Ensembl", MockEnsembl)
    service = _get_assembly_service(Session, file_service)
    with pytest.raises(AssemblyAbortedError) as exc:  # traceback MockHTTPError
        service.prepare_assembly_for_version(1)
    assert str(exc.value) == "Adding assembly for ID '1' aborted."
    assert exc.type == AssemblyAbortedError
    assert file_service.deleted_assemblies == [(9606, "GRCh38")]


def test_get_chain_file_name():
    assert (
        AssemblyService._get_chain_file_name("GRCh37", "GRCh38")
        == "GRCh37_to_GRCh38.chain.gz"
    )


def test_get_organism(Session, file_service, setup):
    service = _get_assembly_service(Session, file_service)
    assert service._get_organism(10090) == "Mus musculus"


def test_get_organism_for_ensembl_url(Session, file_service, setup):
    service = _get_assembly_service(Session, file_service)
    assert service._get_organism_for_ensembl_url(10090) == "mus_musculus"
