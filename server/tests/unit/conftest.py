import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scimodom.database.database import init


@pytest.fixture()
def Session():
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init(engine, lambda: session)

    # from sqlalchemy import inspect
    # insp = inspect(engine)
    # print(f"TABLES CONFTEST={insp.get_table_names()}")

    yield session

    session().rollback()
    session().close()


@pytest.fixture()
def setup():
    from scimodom.database.models import (
        Modomics,
        Taxonomy,
        Taxa,
        Assembly,
        AssemblyVersion,
        DetectionMethod,
    )

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
        Taxa(id=9606, name="Homo Sapiens", short_name="H.Sapiens", taxonomy_id=1),
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
    add.extend(method)

    return add
