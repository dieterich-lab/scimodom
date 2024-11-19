from datetime import datetime
from typing import Iterable

from scimodom.database.models import (
    DataAnnotation,
    Dataset,
    Data,
    DatasetModificationAssociation,
)
from scimodom.services.gene import GeneService


class MockFileService:
    def __init__(self):
        self._genes: list[str] = []

    def update_gene_cache(self, selection_id: int, genes: Iterable[str]) -> None:
        self._genes = []
        for gene in genes:
            self._genes.append(gene)

    def get_gene_cache(self, selection_id: int) -> Iterable[str]:
        if not self._genes:
            raise FileNotFoundError
        else:
            return self._genes


def _get_gene_service(session):
    return GeneService(
        session=session,
        file_service=MockFileService(),
    )


# tests


def test_gene_cache(Session, project, annotation):
    gene_service = _get_gene_service(Session())
    assert gene_service.get_genes([4]) == ["ENSG2", "GENE1", "GENE3"]
    assert gene_service.get_genes([1, 2, 3, 4]) == ["ENSG2", "GENE1", "GENE3"]

    with Session() as session:
        stamp = datetime(2024, 10, 21, 8, 10, 27)
        dataset = Dataset(
            id="ABCDEFGHIJKL",
            title="title",
            organism_id=1,
            technology_id=2,
            modification_type="RNA",
            project_id=project[0].id,
            date_added=stamp,
        )
        data = Data(
            id=99,
            dataset_id="ABCDEFGHIJKL",
            modification_id=1,
            chrom="1",
            start=20652450,
            end=20652451,
            name="m6A",
            score=0,
            strand="-",
            thick_start=20652450,
            thick_end=20652451,
            item_rgb="0,0,0",
            coverage=378,
            frequency=9,
        )
        association = DatasetModificationAssociation(
            dataset_id="ABCDEFGHIJKL", modification_id=1
        )
        data_annotation = DataAnnotation(
            id=99, data_id=99, gene_id="ENSG4", feature="CDS"
        )
        session.add_all([dataset, data, association, data_annotation])
        session.commit()

    gene_service.update_gene_cache(4)
    assert gene_service.get_genes([4]) == ["ENSG2", "GENE1", "GENE3", "GENE4"]
