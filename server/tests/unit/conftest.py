import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scimodom.services.annotation import AnnotationService
from scimodom.database.database import init, Base
from scimodom.database.models import (
    Modomics,
    Taxonomy,
    Taxa,
    Assembly,
    AssemblyVersion,
    Annotation,
    AnnotationVersion,
    DetectionMethod,
)

# EUF version - columns must match "ORM Data model"
EUF_VERSION = "1.7"


@pytest.fixture()
def EUF_version():
    return EUF_VERSION


@pytest.fixture()
def Session():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init(engine, lambda: session)
    Base.metadata.create_all(engine)

    # from sqlalchemy import inspect
    # insp = inspect(engine)
    # print(f"TABLES CONFTEST={insp.get_table_names()}")

    yield session

    session().rollback()
    session().close()


@pytest.fixture()
def setup():
    modomics = [
        Modomics(
            id="6A", name="N6-methyladenosine", short_name="m6A", moiety="nucleoside"
        ),
        Modomics(
            id="5C", name="5-methylcytidine", short_name="m5C", moiety="nucleoside"
        ),
        Modomics(id="9U", name="pseudouridine", short_name="Y", moiety="nucleoside"),
    ]

    taxonomy = [
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Chordata"),
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Arthropoda"),
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Nematoda"),
        Taxonomy(domain="Eukarya", kingdom="Fungi"),
        Taxonomy(domain="Eukarya", kingdom="Plantae"),
        Taxonomy(domain="Bacteria"),
        Taxonomy(domain="Vira"),
    ]

    taxa = [
        Taxa(id=9606, name="Homo sapiens", short_name="H. sapiens", taxonomy_id=1),
        Taxa(id=10090, name="Mus musculus", short_name="M. musculus", taxonomy_id=1),
        Taxa(
            id=7227,
            name="Drosophila melanogaster",
            short_name="D. melanogaster",
            taxonomy_id=2,
        ),
        Taxa(
            id=6239,
            name="Caenorhabditis elegans",
            short_name="C. elegans",
            taxonomy_id=3,
        ),
        Taxa(
            id=4932,
            name="Saccharomyces cerevisiae",
            short_name="S. cerevisiae",
            taxonomy_id=4,
        ),
        Taxa(
            id=3702,
            name="Arabidopsis thaliana",
            short_name="A. thaliana",
            taxonomy_id=5,
        ),
        Taxa(id=562, name="Escherichia coli", short_name="E. coli", taxonomy_id=6),
    ]

    assembly = [
        Assembly(name="GRCh38", taxa_id=9606, version="GcatSmFcytpU"),
        Assembly(name="GRCm38", taxa_id=10090, version="GcatSmFcytpU"),
    ]

    assembly_version = [
        AssemblyVersion(version_num="GcatSmFcytpU"),
    ]

    annotation = [
        Annotation(release=110, taxa_id=9606, version="EyRBnPeVwbzW"),
        Annotation(release=110, taxa_id=10090, version="EyRBnPeVwbzW"),
    ]

    annotation_version = [
        AnnotationVersion(version_num="EyRBnPeVwbzW"),
    ]

    method = [
        DetectionMethod(cls="Quantification", meth="2D-TLC"),
        DetectionMethod(cls="Quantification", meth="LC–MS"),
        DetectionMethod(cls="Locus-specific", meth="Primer extension"),
        DetectionMethod(cls="Locus-specific", meth="RNase H-based"),
        DetectionMethod(cls="Locus-specific", meth="ESI-MS"),
        DetectionMethod(cls="Locus-specific", meth="qPCR-based"),
        DetectionMethod(cls="NGS 2nd generation", meth="Direct sequencing"),
        DetectionMethod(cls="NGS 2nd generation", meth="Chemical-assisted sequencing"),
        DetectionMethod(cls="NGS 2nd generation", meth="Antibody-based sequencing"),
        DetectionMethod(
            cls="NGS 2nd generation", meth="Enzyme/protein-assisted sequencing"
        ),
        DetectionMethod(cls="NGS 3rd generation", meth="Native RNA sequencing"),
        DetectionMethod(cls="NGS 3rd generation", meth="cDNA sequencing"),
    ]

    add = []
    add.extend(modomics)
    add.extend(taxonomy)
    add.extend(taxa)
    add.extend(assembly)
    add.extend(assembly_version)
    add.extend(annotation)
    add.extend(annotation_version)
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
            "modomics_id": "6A",
            "tech": "Technology 1",
            "method_id": 1,
            "organism": {"taxa_id": 9606, "cto": "Cell Type 1", "assembly": "GRCh38"},
        },
        {
            "rna": "mRNA",
            "modomics_id": "6A",
            "tech": "Technology 1",
            "method_id": 1,
            "organism": {"taxa_id": 9606, "cto": "Cell Type 2", "assembly": "GRCh38"},
        },
        {
            "rna": "mRNA",
            "modomics_id": "5C",
            "tech": "Technology 2",
            "method_id": 1,
            "organism": {"taxa_id": 9606, "cto": "Organ 1", "assembly": "GRCh38"},
        },
    ]

    return project


@pytest.fixture(scope="session")
def data_path(tmp_path_factory):
    loc = tmp_path_factory.mktemp("data")
    ASSEMBLY_PATH = loc / "assembly"
    ASSEMBLY_PATH.mkdir()
    ANNOTATION_PATH = loc / "annotation"
    ANNOTATION_PATH.mkdir()
    META_PATH = loc / "metadata"
    META_PATH.mkdir()

    # release 110 see above
    path, annotation_file = AnnotationService.get_annotation_path(
        ANNOTATION_PATH, "Homo_sapiens", "GRCh38", 110, "gtf"
    )
    path.mkdir(parents=True, exist_ok=True)
    Path(path, annotation_file).touch()
    path, chrom_file = AnnotationService.get_chrom_path(
        ANNOTATION_PATH, "Homo_sapiens", "GRCh38"
    )
    path.mkdir(parents=True, exist_ok=True)
    with open(Path(path, chrom_file), "w") as f:
        f.write("1\t1000000")

    yield ASSEMBLY_PATH, ANNOTATION_PATH, META_PATH
