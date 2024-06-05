import logging
from io import StringIO

import pytest

from scimodom.utils.bed_importer import (
    BedImporter,
    BedImportTooManyErrors,
    BedImportEmptyFile,
)
from scimodom.utils.bedtools_dto import Strand


EUF_FILE = """#fileformat=bedRModv1.7
#organism=10090
#modification_type=RNA
#assembly=GRCm39
#annotation_source=Ensembl
#annotation_version=110
#sequencing_platform=HiSeq X Ten
#basecalling=None
#bioinformatics_workflow=https://github.com/liucongcas/GLORI-toolsw
#experiment=https://doi.org/10.1038/s41587-022-01487-9
#external_source=GEO;GSE210563
#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
1\t3528091\t3528092\tm6A\t1000\t+\t3457868\t3457869\t0,205,0\t31\t78
1\t3528096\t3528097\tm6A\t1000\t+\t3457873\t3457874\t0,205,0\t6\t16
1\t3528107\t3528108\tm6A\t1000\t+\t3457884\t3457885\t0,205,0\t5\t24
"""


def test_euf_import():
    stream = StringIO(EUF_FILE)

    importer = BedImporter(stream=stream, source="test", is_euf=True)
    assert importer.get_header("annotation_source") == "Ensembl"

    result = list(importer.parse())
    assert len(result) == 3
    assert result[1].end == 3528097
    assert result[2].strand == Strand.FORWARD
    assert result[0].frequency == 78


BAD_EUF_FILE = """#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
1\t3528091\t3528092\tm6A\t1000\t+\t3457868\t3457869\t0,205,0\t31
1\t3528096\t3528097\tm6A\t1000\t*\t3457873\t3457874\t0,205,0\t6\t16
1\t3528107\t3528108\tm6A\t1000\t+\t3457884\t3457885\t0,205,0\t5\t24
"""


def test_euf_error(caplog):
    stream = StringIO(BAD_EUF_FILE)
    with pytest.raises(BedImportTooManyErrors):
        _ = list(BedImporter(stream=stream, source="test", is_euf=True).parse())
    assert caplog.record_tuples == [
        (
            "scimodom.utils.bed_importer",
            logging.WARNING,
            "test, line 2: Expected 11 fields, but got 10",
        ),
        (
            "scimodom.utils.bed_importer",
            logging.WARNING,
            "test, line 3: '*' is not a valid Strand",
        ),
        (
            "scimodom.utils.bed_importer",
            logging.ERROR,
            "Found too many errors ins 'test' (valid: 1, errors: 2)",
        ),
    ]


EMPTY_EUF_FILE = """#fileformat=bedRModv1.7
#organism=10090
#modification_type=RNA
#assembly=GRCm39
#annotation_source=Ensembl
#annotation_version=110
#sequencing_platform=HiSeq X Ten
#basecalling=None
#bioinformatics_workflow=https://github.com/liucongcas/GLORI-toolsw
#experiment=https://doi.org/10.1038/s41587-022-01487-9
#external_source=GEO;GSE210563
#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency

# More blank lines


"""


def test_empty_euf_file():
    stream = StringIO(EMPTY_EUF_FILE)
    with pytest.raises(BedImportEmptyFile):
        _ = list(BedImporter(stream=stream, source="test", is_euf=True).parse())
