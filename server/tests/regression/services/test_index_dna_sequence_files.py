import gzip
from pathlib import Path

import pysam
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


# BGZF is a series of gzip blocks, each with an extra field "BC" holding
# the block size, and an empty block as end-of-file marker, cf. SAM specs
BGZF_MAGIC = bytes.fromhex("1f8b0804")  # gzip, deflate, FEXTRA flag
BGZF_SUBFIELD = b"BC" + bytes.fromhex("0200")  # id "BC", length 2
BGZF_EOF = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")


def _assert_is_bgzf(path):
    content = Path(path).read_bytes()
    assert content[:4] == BGZF_MAGIC
    assert content[10:12] == bytes.fromhex("0600")  # XLEN
    assert content[12:16] == BGZF_SUBFIELD
    assert content[-len(BGZF_EOF) :] == BGZF_EOF


@pytest.fixture
def test_data(tmp_path):
    # add required assembly files
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    d.mkdir(parents=True, exist_ok=True)


@pytest.mark.datafiles(
    Path(DATA_DIR, "Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz"),
)
def test_index_dna_sequence_file(
    Session,
    datafiles,
    tmp_path,
    test_data,
    setup,
):
    d = tmp_path / "t_data" / FileService.ASSEMBLY_DEST / "Homo_sapiens" / "GRCh38"
    filen = "Homo_sapiens.GRCh38.dna.chromosome.1.fa.gz"
    Path(datafiles, filen).rename(d / filen)
    with gzip.open(Path(d, filen), "rt") as fh:
        expected = "".join(fh.read().split("\n")[1:])  # w/o header

    # plain gzip before
    assert Path(d, filen).read_bytes()[4:] != BGZF_MAGIC

    file_service = _get_file_service(Session, tmp_path)
    file_service.index_dna_sequence_file(9606, "1")

    _assert_is_bgzf(Path(d, filen))
    # random access works with the index, and the sequence is unchanged
    with pysam.FastaFile(Path(d, filen).as_posix()) as fasta:
        assert list(fasta.references) == ["1"]
        assert fasta.get_reference_length("1") == 1200
        assert fasta.fetch("1") == expected
        assert fasta.fetch("1", 100, 160) == expected[100:160]

    assert Path(d, f"{filen}.gzi").exists()

    with open(Path(d, f"{filen}.fai"), "r") as fh:
        lines = fh.readlines()
    assert lines == ["1\t1200\t34\t60\t61\n"]
