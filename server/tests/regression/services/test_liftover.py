from pathlib import Path

import pytest

from scimodom.services.assembly import AssemblyService
from scimodom.services.external import ExternalService
from scimodom.services.file import FileService

from tests.mocks.web import MockWebService

DATA_DIR = Path(Path(__file__).parents[1], "data")

LIFTED_RECORDS = [
    "1\t1342388\t1342389\tm5C\t10\t-\t1277768\t1277769\t0,0,0\t10\t25",
    "16\t773225\t773226\tm5C\t20\t+\t823225\t823226\t0,0,0\t20\t25",
    "19\t54174337\t54174338\tm5C\t30\t-\t54678031\t54678032\t0,0,0\t30\t25",
    "2\t80140428\t80140429\tm5C\t40\t-\t80367554\t80367555\t0,0,0\t40\t25",
    "22\t41620864\t41620865\tm5C\t50\t-\t42016868\t42016869\t0,0,0\t50\t25",
    "3\t48634041\t48634042\tm5C\t60\t-\t48671474\t48671475\t0,0,0\t60\t25",
    "MT\t14698\t14699\tm5C\t70\t-\t14698\t14699\t0,0,0\t70\t25",
    "X\t24077264\t24077265\tm5C\t80\t+\t24095381\t24095382\t0,0,0\t80\t25",
]


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


def _get_web_service():
    return MockWebService()


def _get_external_service(Session, tmp_path):
    return ExternalService(file_service=_get_file_service(Session, tmp_path))


def _get_assembly_service(Session, tmp_path):
    return AssemblyService(
        session=Session(),
        external_service=_get_external_service(Session, tmp_path),
        web_service=_get_web_service(),
        file_service=_get_file_service(Session, tmp_path),
    )


@pytest.fixture
def test_data(tmp_path):
    # add required assembly files
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh37"
    d.mkdir(parents=True, exist_ok=True)
    return d


# tests


# NOTE: CrossMap updates “chrom”, “start”, “end”, and “strand” only. Thick values
# are overwritten by ValidatorService._do_lift_over; here we are only testing
# if the CrossMap output is reproducible, hence thick values remain unchanged.
# cf. tests/unit/services/test_validator.py::test_validate_lifted_records


@pytest.mark.datafiles(Path(DATA_DIR, "GRCh37_to_GRCh38.chain.gz"))
@pytest.mark.datafiles(Path(DATA_DIR, "raw.bedrmod"))
def test_liftover(Session, datafiles, tmp_path, test_data, setup):
    filen = "GRCh37_to_GRCh38.chain.gz"
    Path(datafiles, filen).rename(test_data / filen)

    assembly_service = _get_assembly_service(Session, tmp_path)
    assembly = assembly_service.get_by_id(3)
    with assembly_service.create_lifted_file(
        assembly, Path(datafiles, "raw.bedrmod")
    ) as fp:
        lines = fp.read().splitlines()
    assert lines == LIFTED_RECORDS
