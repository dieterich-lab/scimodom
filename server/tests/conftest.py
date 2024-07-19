from collections import namedtuple
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scimodom.database.database import init, Base
from scimodom.utils.specifications import SPECS_EUF

# data path
DataPath = namedtuple("DataPath", "LOC ASSEMBLY_PATH ANNOTATION_PATH META_PATH")

pytest_plugins = [
    "tests.fixtures.setup",
    "tests.fixtures.selection",
    "tests.fixtures.project",
    "tests.fixtures.dataset",
]


@pytest.fixture()
def Session():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init(engine, lambda: session)
    Base.metadata.create_all(engine)

    yield session

    session().rollback()
    session().close()


# TODO this is now only used in integration/test_import_data
@pytest.fixture(scope="session")
def data_path(tmp_path_factory):
    format = SPECS_EUF["format"]
    version = SPECS_EUF["versions"][-1]
    loc = tmp_path_factory.mktemp("data")
    ASSEMBLY_PATH = loc / "assembly"
    ASSEMBLY_PATH.mkdir()
    ANNOTATION_PATH = loc / "annotation"
    ANNOTATION_PATH.mkdir()
    META_PATH = loc / "metadata"
    META_PATH.mkdir()

    SUB_PATH = loc / "metadata" / "project_requests"
    SUB_PATH.mkdir()

    with open(Path(loc, "test.bed"), "w") as f:
        f.write(f"#fileformat={format}v{version}\n")
        f.write("#organism=9606\n")
        f.write("#modification_type=RNA\n")
        f.write("#assembly=GRCh38\n")
        f.write("#annotation_source=Annotation\n")
        f.write("#annotation_version=Version\n")
        f.write("#sequencing_platform=Sequencing platform\n")
        f.write("#basecalling=\n")
        f.write("#bioinformatics_workflow=Workflow\n")
        f.write("#experiment=Description of experiment.\n")
        f.write("#external_source=\n")
        f.write(
            "#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency\n"
        )
        f.write("1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")

    with open(Path(loc, "test_header_fail.bed"), "w") as f:
        f.write(f"#fileformat={format}v{version}\n")
        f.write("#organism=9606\n")
        f.write("#modification_type=RNA\n")
        f.write("#assembly=\n")
        f.write("#annotation_source=Annotation\n")
        f.write("#annotation_version=Version\n")
        f.write("#sequencing_platform=Sequencing platform\n")
        f.write("#basecalling=\n")
        f.write("#bioinformatics_workflow=Workflow\n")
        f.write("#experiment=Description of experiment.\n")
        f.write("#external_source=\n")
        f.write(
            "#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency\n"
        )
        f.write("1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")

    with open(Path(loc, "test_data_fail.bed"), "w") as f:
        f.write(f"#fileformat={format}v{version}\n")
        f.write("#organism=9606\n")
        f.write("#modification_type=RNA\n")
        f.write("#assembly=GRCh38\n")
        f.write("#annotation_source=Annotation\n")
        f.write("#annotation_version=Version\n")
        f.write("#sequencing_platform=Sequencing platform\n")
        f.write("#basecalling=\n")
        f.write("#bioinformatics_workflow=Workflow\n")
        f.write("#experiment=Description of experiment.\n")
        f.write("#external_source=\n")
        f.write(
            "#chrom\tchromstart\tchromEnd\tname\tscore\tstrand\tthickstart\tthickEnd\titermRgb\tcoverage\tfrequency\textra1\textra2\n"
        )
        f.write("1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")
        f.write("1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\textra1\textra2\n")
        f.write("\n")
        f.write("1\ta\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")
        f.write("\t-1\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")
        f.write("A\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t1\n")
        f.write("1\t0\t10\tm6A\t1000\t\t0\t10\t0,0,0\t10\t1\n")
        f.write("1\t0\t10\tm5C\t1000\t+\t0\t10\t0,0,0\t10\t1\n")
        f.write("1\t0\t10\tm5C\t1000\t+\n")
        f.write("1\t0\t10\n")
        f.write("1\t0\t10\tm6A\t1000\t+\t0\t10\t0,0,0\t10\t200\n")
        f.write("1;0;10;m6A;1000;+;0;10;0,0,0;10;200\n")
        f.write("1,0,10,m6A,1000,+,0,10,'0,0,0',10,200")

    yield DataPath(loc, ASSEMBLY_PATH, ANNOTATION_PATH, META_PATH)
