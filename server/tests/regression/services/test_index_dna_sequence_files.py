from pathlib import Path
from subprocess import run

import pytest

from scimodom.services.file import FileService

DATA_DIR = Path(Path(__file__).parents[1], "data")


def _get_file_service(Session, tmp_path):
    return FileService(
        session=Session(),
        data_path=Path(tmp_path, "t_data"),
        temp_path=Path(tmp_path, "t_temp"),
        upload_path=Path(tmp_path, "t_upload"),
        import_path=Path(tmp_path, "t_import"),
    )


@pytest.fixture
def test_data(tmp_path):
    # add required assembly files
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)


@pytest.mark.datafiles(Path(DATA_DIR, "Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz"))
def test_index_dna_sequence_file(Session, datafiles, tmp_path, test_data, setup):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    filen = "Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz"
    Path(datafiles, filen).rename(d / filen)

    file_service = _get_file_service(Session, tmp_path)
    file_service.index_dna_sequence_file(9606, "1")

    file_cmd = run(["file", "-b", Path(d, filen).as_posix()], capture_output=True)
    assert (
        file_cmd.stdout
        == b"Blocked GNU Zip Format (BGZF; gzip compatible), block length 414\n"
    )

    with open(Path(d, f"{filen}.fai"), "r") as fh:
        lines = fh.readlines()
    assert lines == ["1\t1200\t34\t60\t61\n"]

    assert Path(d, f"{filen}.gzi").exists()
