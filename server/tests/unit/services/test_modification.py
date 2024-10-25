from collections import namedtuple

import pytest
from sqlalchemy import select, func

from scimodom.database.models import (
    Annotation,
    AnnotationVersion,
    Data,
    DataAnnotation,
    Dataset,
    DetectionTechnology,
    GenomicAnnotation,
    Organism,
)
from scimodom.services.modification import ModificationService
from scimodom.utils.specs.enums import Strand, AnnotationSource

Coord = namedtuple("Coord", "chrom start end")

RECORDS = [
    {
        "id": 4,
        "chrom": "1",
        "start": 20652450,
        "end": 20652451,
        "name": "m6A",
        "score": 0,
        "strand": Strand.REVERSE,
        "coverage": 378,
        "frequency": 9,
        "dataset_id": "dataset_id03",
        "feature": "CDS,Exonic",
        "gene_id": "ENSG1",
        "gene_name": "GENE1",
        "gene_biotype": "protein_coding",
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 5,
        "chrom": "1",
        "start": 87328672,
        "end": 87328673,
        "name": "m6A",
        "score": 0,
        "strand": Strand.FORWARD,
        "coverage": 183,
        "frequency": 6,
        "dataset_id": "dataset_id03",
        "feature": "Intergenic",
        "gene_id": "ENSIntergenic",
        "gene_name": None,
        "gene_biotype": None,
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 6,
        "chrom": "1",
        "start": 104153268,
        "end": 104153269,
        "name": "m6A",
        "score": 0,
        "strand": Strand.REVERSE,
        "coverage": 183,
        "frequency": 4,
        "dataset_id": "dataset_id03",
        "feature": None,
        "gene_id": None,
        "gene_name": None,
        "gene_biotype": None,
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 7,
        "chrom": "1",
        "start": 194189297,
        "end": 194189298,
        "name": "m6A",
        "score": 0,
        "strand": Strand.FORWARD,
        "coverage": 19,
        "frequency": 47,
        "dataset_id": "dataset_id03",
        "feature": "Intronic,Exonic",
        "gene_id": "ENSG2,ENSG3",
        "gene_name": "ENSG2,GENE3",
        "gene_biotype": "lncRNA,processed_pseudogene",
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 1,
        "chrom": "17",
        "start": 100001,
        "end": 100002,
        "name": "m6A",
        "score": 1000,
        "strand": Strand.FORWARD,
        "coverage": 43,
        "frequency": 100,
        "dataset_id": "dataset_id01",
        "feature": None,
        "gene_id": None,
        "gene_name": None,
        "gene_biotype": None,
        "tech": "Technology 1",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 4,
        "chrom": "1",
        "start": 20652450,
        "end": 20652451,
        "name": "m6A",
        "score": 0,
        "strand": Strand.REVERSE,
        "coverage": 378,
        "frequency": 9,
        "dataset_id": "dataset_id03",
        "feature": "CDS",
        "gene_id": "ENSG1",
        "gene_name": "GENE1",
        "gene_biotype": "protein_coding",
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
    {
        "id": 7,
        "chrom": "1",
        "start": 194189297,
        "end": 194189298,
        "name": "m6A",
        "score": 0,
        "strand": Strand.FORWARD,
        "coverage": 19,
        "frequency": 47,
        "dataset_id": "dataset_id03",
        "feature": "Intronic",
        "gene_id": "ENSG2",
        "gene_name": "ENSG2",
        "gene_biotype": "lncRNA",
        "tech": "Technology 2",
        "taxa_id": 9606,
        "cto": "Cell type 1",
        "reference_id": 96,
    },
]


class MockAnnotationService:
    def __init__(self, session):
        self._session = session
        self._version = self._session.execute(
            select(AnnotationVersion.version_num)
        ).scalar_one()

    def get_annotation(
        self, annotation_source: AnnotationSource, taxa_id: int
    ) -> Annotation:
        return self._session.execute(
            select(Annotation).filter_by(
                taxa_id=taxa_id, source=annotation_source.value, version=self._version
            )
        ).scalar_one()


def _mock_get_base_search_query(isouter=False):
    query = (
        select(
            Data.id,
            Data.chrom,
            Data.start,
            Data.end,
            Data.name,
            Data.score,
            Data.strand,
            Data.coverage,
            Data.frequency,
            Data.dataset_id,
            func.group_concat(DataAnnotation.feature.distinct()).label("feature"),
            func.group_concat(
                GenomicAnnotation.id.distinct()  # .op("ORDER BY")(GenomicAnnotation.id)
            ).label("gene_id"),
            func.group_concat(
                GenomicAnnotation.name.distinct()  # .op("ORDER BY")(GenomicAnnotation.id)
            ).label("gene_name"),
            func.group_concat(
                GenomicAnnotation.biotype.distinct()  # .op("ORDER BY")(GenomicAnnotation.id)
            ).label("gene_biotype"),
            DetectionTechnology.tech,
            Organism.taxa_id,
            Organism.cto,
        )
        .join_from(Data, DataAnnotation, Data.annotations, isouter=isouter)
        .join_from(
            DataAnnotation,
            GenomicAnnotation,
            DataAnnotation.inst_genomic,
            isouter=isouter,
        )
        .join_from(Data, Dataset, Data.inst_dataset)
        .join_from(Dataset, DetectionTechnology, Dataset.inst_technology)
        .join_from(Dataset, Organism, Dataset.inst_organism)
    )
    return query


def _get_modification_service(session):
    return ModificationService(
        session=session, annotation_service=MockAnnotationService(session)
    )


# tests


@pytest.mark.parametrize(
    "technology_ids,coord,gene_filter,multi_sort,first_record,max_records,expected_records,total",
    [
        ([1], Coord(None, 0, None), [], [], 0, 10, [RECORDS[4]], 1),
        ([1, 2], Coord(None, 0, None), [], [], 0, 10, RECORDS[:5], 5),
        ([1, 2], Coord("1", 20000000, 30000000), [], [], 0, 10, [RECORDS[0]], 1),
        (
            [1, 2],
            Coord(None, 0, None),
            ["gene_name%2BGENE1%2BstartsWith", "feature%2BCDS%2Bin"],
            [],
            0,
            10,
            [RECORDS[5]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            ["gene_biotype%2BlncRNA%2Bin"],
            [],
            0,
            10,
            [RECORDS[6]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            [],
            ["chrom%2Bdesc"],
            0,
            10,
            [RECORDS[4], RECORDS[0], RECORDS[1], RECORDS[2], RECORDS[3]],
            5,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            [],
            ["coverage%2Bdesc", "frequency%2Bdesc"],
            0,
            10,
            [RECORDS[0], RECORDS[1], RECORDS[2], RECORDS[4], RECORDS[3]],
            5,
        ),
        ([1, 2], Coord(None, 0, None), [], [], 1, 2, RECORDS[1:3], 5),
    ],
)
def test_get_modifications_by_source(
    technology_ids,
    coord,
    gene_filter,
    multi_sort,
    first_record,
    max_records,
    expected_records,
    total,
    Session,
    mocker,
    annotation,
):  # noqa
    modification_service = _get_modification_service(Session())
    # patch base query, cf. #154
    mocker.patch.object(
        modification_service, "_get_base_search_query", _mock_get_base_search_query
    )

    response = modification_service.get_modifications_by_source(
        annotation_source=AnnotationSource.ENSEMBL,
        modification_id=1,
        organism_id=1,
        technology_ids=technology_ids,
        taxa_id=9606,
        gene_filter=gene_filter,
        chrom=coord.chrom,
        chrom_start=coord.start,
        chrom_end=coord.end,
        first_record=first_record,
        max_records=max_records,
        multi_sort=multi_sort,
    )
    assert response["totalRecords"] == total
    assert response["records"] == expected_records


def test_get_modifications_by_gene(Session, mocker, annotation):  # noqa
    modification_service = _get_modification_service(Session())
    # patch base query, cf. #154
    mocker.patch.object(
        modification_service, "_get_base_search_query", _mock_get_base_search_query
    )

    response = modification_service.get_modifications_by_gene(
        annotation_source=AnnotationSource.ENSEMBL,
        taxa_id=9606,
        gene_filter=["gene_name%2BGENE1%2BstartsWith"],
        chrom=None,
        chrom_start=0,
        chrom_end=None,
        first_record=0,
        max_records=10,
        multi_sort=[],
    )
    assert response["totalRecords"] == 1
    assert response["records"] == [RECORDS[0]]


def test_get_modification_site(Session, dataset):  # noqa
    modification_service = _get_modification_service(Session())
    response = modification_service.get_modification_site("17", 100001, 100002)
    assert len(response["records"]) == 2
    assert response["records"][0]["dataset_id"] == "dataset_id01"
    assert response["records"][1]["dataset_id"] == "dataset_id02"
    assert response["records"][0]["cto"] == "Cell type 1"
    assert response["records"][1]["cto"] == "Cell type 2"
    assert response["records"][0]["tech"] == "Technology 1"
    assert response["records"][1]["tech"] == "Technology 2"
    assert response["records"][0]["score"] == 1000
    assert response["records"][1]["score"] == 10
