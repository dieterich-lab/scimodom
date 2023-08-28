import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scimodom.database.database import init


@pytest.fixture(scope="session")
def Session():
    engine = create_engine('sqlite:///:memory:')
    session = sessionmaker(autocommit=False,
                           autoflush=False,
                           bind=engine)
    init(engine, lambda: session)
    
    #from sqlalchemy import inspect
    #insp = inspect(engine)
    #print(f"TABLES CONFTEST={insp.get_table_names()}")
    
    yield session
    
    session().rollback()
    session().close()
    
    
@pytest.fixture(scope="session")
def setup():
    
    from scimodom.database.models import Modomics, Taxonomy, Taxa, Assembly
    
    modomics = [
        Modomics(id="6A", name="N6-methyladenosine", short_name="m6A", moiety="nucleoside"),
        Modomics(id="5C", name="5-methylcytidine", short_name="m5C", moiety="nucleoside"),
        Modomics(id="9U", name="pseudouridine", short_name="Y", moiety="nucleoside")
    ]
    
    taxonomy = [
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Chordata"),
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Arthropoda"),
        Taxonomy(domain="Eukarya", kingdom="Animalia", phylum="Nematoda"),
        Taxonomy(domain="Eukarya", kingdom="Fungi"),
        Taxonomy(domain="Eukarya", kingdom="Plantae"),
        Taxonomy(domain="Bacteria"),
        Taxonomy(domain="Vira")
    ]
    
    taxa = [
        Taxa(id=9606, name="Homo Sapiens", short_name="H.Sapiens", taxonomy_id=1),
        Taxa(id=10090, name="Mus musculus", short_name="M. musculus", taxonomy_id=1),
        Taxa(id=7227, name="Drosophila melanogaster", short_name="D. melanogaster", taxonomy_id=2),
        Taxa(id=6239, name="Caenorhabditis elegans", short_name="C. elegans", taxonomy_id=3),
        Taxa(id=4932, name="Saccharomyces cerevisiae", short_name="S. cerevisiae", taxonomy_id=4),
        Taxa(id=3702, name="Arabidopsis thaliana", short_name="A. thaliana", taxonomy_id=5),
        Taxa(id=562, name="Escherichia coli", short_name="E. coli", taxonomy_id=6)
    ]

    assembly = [
        Assembly(name="GRCh38", taxa_id=9696),
        Assembly(name="GRCm38", taxa_id=10090)
    ]
    
    add = []
    add.extend(modomics)
    add.extend(taxonomy)
    add.extend(taxa)
    add.extend(assembly)
    
    return add 




    
    
    
    
    
    
    
    
    
    
    
    

    
    
