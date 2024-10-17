import logging
from io import StringIO

import pytest

from scimodom.utils.importer.bed_importer import (
    Bed6Importer,
    BedImportTooManyErrors,
    BedImportEmptyFile,
    EufImporter,
)
from scimodom.utils.specs.enums import Strand

EUF_FILE = """#fileformat=bedRModv1.8
#organism=10090
#modification_type=RNA
#assembly=GRCm39
#annotation_source=Ensembl
#annotation_version=110
#sequencing_platform=HiSeq X Ten
#basecalling=
#bioinformatics_workflow=
#experiment=
#external_source=GEO;GSE123456
#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency
1\t3528091\t3528092\tm6A\t1000\t+\t3457868\t3457869\t0,205,0\t31\t78
1\t3528096\t3528097\tm6A\t1000\t+\t3457873\t3457874\t0,205,0\t6\t16
1\t3528107\t3528108\tm6A\t1000\t+\t3457884\t3457885\t0,205,0\t5\t24
"""


def test_euf_import():
    stream = StringIO(EUF_FILE)

    importer = EufImporter(stream=stream, source="test")
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
    importer = EufImporter(stream=stream, source="test")
    with pytest.raises(BedImportTooManyErrors):
        _ = list(importer.parse())
    assert caplog.record_tuples == [
        (
            "scimodom.utils.importer.bed_importer",
            logging.WARNING,
            "test, line 2: Expected 11 fields, but got 10",
        ),
        (
            "scimodom.utils.importer.bed_importer",
            logging.WARNING,
            "test, line 3: '*' is not a valid Strand",
        ),
        (
            "scimodom.utils.importer.bed_importer",
            logging.ERROR,
            "Found too many errors in test (valid: 1, errors: 2)",
        ),
    ]
    assert (
        importer.get_error_summary()
        == """test, line 2: Expected 11 fields, but got 10
test, line 3: '*' is not a valid Strand
"""
    )


def test_euf_error_without_error_rate(caplog):
    stream = StringIO(BAD_EUF_FILE)
    result = list(
        EufImporter(stream=stream, source="test", max_error_rate=None).parse()
    )

    assert len(result) == 1
    assert caplog.record_tuples == [
        (
            "scimodom.utils.importer.bed_importer",
            logging.WARNING,
            "test, line 2: Expected 11 fields, but got 10",
        ),
        (
            "scimodom.utils.importer.bed_importer",
            logging.WARNING,
            "test, line 3: '*' is not a valid Strand",
        ),
    ]


EMPTY_EUF_FILE = """#fileformat=bedRModv1.8
#organism=10090
#modification_type=RNA
#assembly=GRCm39
#annotation_source=Ensembl
#annotation_version=110
#sequencing_platform=HiSeq X Ten
#basecalling=
#bioinformatics_workflow=
#experiment=
#external_source=GEO;GSE123456
#chrom\tchromStart\tchromEnd\tname\tscore\tstrand\tthickStart\tthickEnd\titemRgb\tcoverage\tfrequency

# More blank lines


"""


def test_empty_euf_file():
    stream = StringIO(EMPTY_EUF_FILE)
    with pytest.raises(BedImportEmptyFile):
        _ = list(EufImporter(stream=stream, source="test").parse())


BED6_FILE = """1\t3528091\t3528092\tm6A\t1000\t+
1\t3528096\t3528097\tm6A\t1000\t+
1\t3528107\t3528108\tm6A\t1000\t+
"""


def test_bed_6_file():
    stream = StringIO(BED6_FILE)
    importer = Bed6Importer(stream=stream, source="test")

    result = list(importer.parse())
    assert len(result) == 3
    assert result[1].end == 3528097
    assert result[2].strand == Strand.FORWARD
