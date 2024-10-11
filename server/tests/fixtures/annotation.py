import pytest

from scimodom.database.models import GenomicAnnotation, DataAnnotation


@pytest.fixture
def annotation(Session, dataset):
    genomic_annotation1 = GenomicAnnotation(
        id="ENSG1", annotation_id=1, name="GENE1", biotype="protein_coding"
    )
    genomic_annotation2 = GenomicAnnotation(
        id="ENSMUSG1", annotation_id=2, name="Gene1", biotype="protein_coding"
    )
    genomic_annotation3 = GenomicAnnotation(
        id="ENSIntergenic", annotation_id=1, name=None, biotype=None
    )
    genomic_annotation4 = GenomicAnnotation(
        id="ENSG2", annotation_id=1, name="ENSG2", biotype="lncRNA"
    )
    genomic_annotation5 = GenomicAnnotation(
        id="ENSG3", annotation_id=1, name="GENE3", biotype="processed_pseudogene"
    )
    data_annotation1 = DataAnnotation(
        id=1, data_id=4, gene_id="ENSG1", feature="Exonic"
    )
    data_annotation2 = DataAnnotation(id=2, data_id=4, gene_id="ENSG1", feature="CDS")
    data_annotation3 = DataAnnotation(
        id=3, data_id=5, gene_id="ENSIntergenic", feature="Intergenic"
    )
    data_annotation4 = DataAnnotation(
        id=4, data_id=7, gene_id="ENSG2", feature="Intronic"
    )
    data_annotation5 = DataAnnotation(
        id=5, data_id=7, gene_id="ENSG3", feature="Exonic"
    )
    session = Session()
    session.add_all(
        [
            genomic_annotation1,
            genomic_annotation2,
            genomic_annotation3,
            genomic_annotation4,
            genomic_annotation5,
            data_annotation1,
            data_annotation2,
            data_annotation3,
            data_annotation4,
            data_annotation5,
        ]
    )
    session.commit()
