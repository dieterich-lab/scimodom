from collections import namedtuple
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scimodom.database.database import init, Base
from scimodom.database.models import (
    RNAType,
    Modomics,
    Taxonomy,
    Taxa,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    DetectionMethod,
)
from scimodom.utils.specifications import SPECS_EUF

# data path
DataPath = namedtuple("DataPath", "LOC ASSEMBLY_PATH ANNOTATION_PATH META_PATH")


@pytest.fixture()
def EUF_specs():
    # columns must match "ORM Data/Dataset model"
    FMT = SPECS_EUF["format"]
    VERSION = SPECS_EUF["versions"][-1]
    return FMT, VERSION, SPECS_EUF[VERSION]


@pytest.fixture()
def Session():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init(engine, lambda: session)
    Base.metadata.create_all(engine)

    yield session

    session().rollback()
    session().close()


@pytest.fixture()
def setup():
    add = []
    rna_types = [RNAType(id="WTS", name="whole transcriptome")]
    add.extend(rna_types)
    modomics = [
        Modomics(
            id="2000000006A",
            name="N6-methyladenosine",
            short_name="m6A",
            moiety="nucleoside",
        ),
        Modomics(
            id="2000000005C",
            name="5-methylcytidine",
            short_name="m5C",
            moiety="nucleoside",
        ),
        Modomics(
            id="2000000009U", name="pseudouridine", short_name="Y", moiety="nucleoside"
        ),
    ]
    add.extend(modomics)
    taxonomy = [
        Taxonomy(
            id="a1b240af", domain="Eukarya", kingdom="Animalia", phylum="Chordata"
        ),
        Taxonomy(
            id="455a3823", domain="Eukarya", kingdom="Animalia", phylum="Arthropoda"
        ),
    ]
    add.extend(taxonomy)
    taxa = [
        Taxa(
            id=9606,
            name="Homo sapiens",
            short_name="H. sapiens",
            taxonomy_id="a1b240af",
        ),
        Taxa(
            id=10090,
            name="Mus musculus",
            short_name="M. musculus",
            taxonomy_id="a1b240af",
        ),
        Taxa(
            id=7227,
            name="Drosophila melanogaster",
            short_name="D. melanogaster",
            taxonomy_id="455a3823",
        ),
    ]
    add.extend(taxa)
    assembly_version = [
        AssemblyVersion(version_num="GcatSmFcytpU"),
    ]
    add.extend(assembly_version)
    assembly = [
        Assembly(name="GRCh38", alt_name="hg38", taxa_id=9606, version="GcatSmFcytpU"),
        Assembly(name="GRCm38", alt_name="mm10", taxa_id=10090, version="GcatSmFcytpU"),
        Assembly(name="GRCh37", alt_name="hg19", taxa_id=9606, version="J9dit7Tfc6Sb"),
    ]
    add.extend(assembly)
    annotation_version = [
        AnnotationVersion(version_num="EyRBnPeVwbzW"),
    ]
    add.extend(annotation_version)
    annotation = [
        Annotation(release=110, taxa_id=9606, source="ensembl", version="EyRBnPeVwbzW"),
        Annotation(
            release=110, taxa_id=10090, source="ensembl", version="EyRBnPeVwbzW"
        ),
        Annotation(release=109, taxa_id=9606, source="ensembl", version="A8syx5TzWlK0"),
    ]
    add.extend(annotation)
    method = [
        DetectionMethod(
            id="0ee048bc", cls="NGS 2nd generation", meth="Chemical-assisted sequencing"
        ),
        DetectionMethod(
            id="91b145ea", cls="NGS 2nd generation", meth="Antibody-based sequencing"
        ),
        DetectionMethod(
            id="01d26feb",
            cls="NGS 2nd generation",
            meth="Enzyme/protein-assisted sequencing",
        ),
    ]
    add.extend(method)
    return add


@pytest.fixture()
def project_template():
    """\
    2023-08-25 Project template (JSON format).

    All keys are required.
    "external_sources" can be None (null in yml).
    "external_sources" and "metadata" can be list of dict, or dict.

    Parameters
    ----------
    external_sources_fmt: str or None
        "external_sources" format (list, dict, or None)
    metadata_fmt: str
        "metadata" format (list or dict)
    missing_key: str or None
        missing_key

    Returns
    -------
    dict
        Project template
    """

    project = dict()
    project["title"] = "Title"
    project["summary"] = "Summary"
    project["contact_name"] = "Contact Name"
    project["contact_institution"] = "Contact Institution"
    project["contact_email"] = "Contact Email"
    project["date_published"] = "2024-01-01"
    project["external_sources"] = [
        {"doi": "DOI1", "pmid": None},
        {"doi": "DOI2", "pmid": 22222222},
    ]
    project["metadata"] = [
        {
            "rna": "mRNA",
            "modomics_id": "2000000006A",
            "tech": "Technology 1",
            "method_id": "01d26feb",
            "organism": {"taxa_id": 9606, "cto": "Cell Type 1", "assembly": "GRCh38"},
        },
        {
            "rna": "mRNA",
            "modomics_id": "2000000006A",
            "tech": "Technology 1",
            "method_id": "01d26feb",
            "organism": {"taxa_id": 9606, "cto": "Cell Type 2", "assembly": "GRCh38"},
        },
        {
            "rna": "mRNA",
            "modomics_id": "2000000005C",
            "tech": "Technology 2",
            "method_id": "01d26feb",
            "organism": {"taxa_id": 9606, "cto": "Organ 1", "assembly": "GRCh38"},
        },
        {
            "rna": "mRNA",
            "modomics_id": "2000000005C",
            "tech": "Technology 1",
            "method_id": "01d26feb",
            "organism": {"taxa_id": 9606, "cto": "Cell Type 1", "assembly": "GRCh38"},
        },
    ]

    return project


# TODO this should be simplified to have only temp dirs fixture for session-wise
# usage, i.e. top of function, the rest should be handlded in separate tests
# does it actually have to be session-wise???
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
