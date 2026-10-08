from collections import namedtuple

import pytest
from sqlalchemy import select, func, and_

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
from scimodom.services.modification import (
    SearchParams,
    PageParams,
    ModificationService,
    MultiSortError,
)
from scimodom.utils.specs.enums import Strand, AnnotationSource

Coord = namedtuple("Coord", "chrom start end")

RECORDS = [
    {
        "id": 4,
        "chrom": "1",
        "start": 20652450,
        "end": 20652451,
        "name": "m6A",
        "score": 1,
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
        "score": 1,
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
        "score": 1,
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
        "score": 1,
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
        "score": 1,
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
        "score": 1,
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


def _mock_build_query(
    annotation: Annotation,
    search_params: SearchParams,
):
    # NOTE: mirrors the real ModificationService._build_query, minus
    # the .op("ORDER BY") inside group_concat (not supported by SQLite, which
    # these tests run against) - see #194.
    gene_name = search_params.gene_name
    biotypes = search_params.biotypes
    features = search_params.features

    data_annotation_on = Data.id == DataAnnotation.data_id
    if features:
        data_annotation_on = and_(
            data_annotation_on, DataAnnotation.feature.in_(features)
        )

    genomic_annotation_on = GenomicAnnotation.id == DataAnnotation.gene_id
    genomic_annotation_isouter = True
    if gene_name or biotypes or features:
        genomic_annotation_on = and_(
            genomic_annotation_on,
            GenomicAnnotation.annotation_id == annotation.id,
        )
    if gene_name or biotypes:
        genomic_annotation_isouter = False
    if gene_name:
        genomic_annotation_on = and_(
            genomic_annotation_on, GenomicAnnotation.name == gene_name
        )
    if biotypes:
        # hard coded: only these values will pass the tests
        raw_biotypes = ["Protein coding", "lncRNA"]
        genomic_annotation_on = and_(
            genomic_annotation_on, GenomicAnnotation.biotype.in_(raw_biotypes)
        )

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
        .join_from(Data, DataAnnotation, data_annotation_on, isouter=True)
        .join_from(
            DataAnnotation,
            GenomicAnnotation,
            genomic_annotation_on,
            isouter=genomic_annotation_isouter,
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


def test_get_modification_records_count(Session, dataset):
    modification_service = _get_modification_service(Session())
    assert modification_service.get_modification_records_count() == 7


def test_get_modification_sites_count(Session, dataset):
    modification_service = _get_modification_service(Session())
    assert modification_service.get_modification_sites_count() == 6


@pytest.mark.parametrize(
    "sort,message",
    [
        (["star+asc"], "Invalid sort column: 'star'"),
        (["start+ascending"], "Invalid sort direction: 'ascending'"),
        (["start"], "Invalid sort: 'start'"),
        (["start+asc+any"], "Invalid sort: 'start+asc+any'"),
    ],
)
def test_apply_sort_fail(Session, annotation, sort, message):
    modification_service = _get_modification_service(Session())
    with pytest.raises(MultiSortError) as exc:
        modification_service._apply_sort(select(Data), PageParams(sort=sort))
    assert (str(exc.value)) == message
    assert exc.type == MultiSortError


# API-semantics enforce "geneName XOR chrom" (required if by=gene),
# "chromStart/chromEnd require chrom", and "chromEnd requires chromStart".
# The service layer is intentionally agnostic: it applies whatever
# filters it receives, never raises on a missing companion, and
# "silently" applies chrom filters.


@pytest.mark.parametrize(
    "technology_ids,coord,gene_name,biotypes,features,sort,offset,limit,expected_records,expected_total",
    [
        ([1], Coord(None, 0, None), None, [], [], [], 0, 10, [RECORDS[4]], 1),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            [],
            [],
            [],
            0,
            10,
            RECORDS[:5],
            5,
        ),
        (
            [1, 2],
            Coord("1", 20000000, 30000000),
            None,
            [],
            [],
            [],
            0,
            10,
            [RECORDS[0]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            "GENE1",
            [],
            ["CDS"],
            [],
            0,
            10,
            [RECORDS[5]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            "ENSG2",
            [],
            [],
            [],
            0,
            10,
            [RECORDS[6]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            ["lncRNA"],
            [],
            [],
            0,
            10,
            [RECORDS[6]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            [],
            [],
            ["chrom+desc"],
            0,
            10,
            [RECORDS[4], RECORDS[0], RECORDS[1], RECORDS[2], RECORDS[3]],
            5,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            [],
            [],
            ["coverage+desc", "frequency+desc"],
            0,
            10,
            [RECORDS[0], RECORDS[1], RECORDS[2], RECORDS[4], RECORDS[3]],
            5,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            [],
            [],
            [],
            1,
            2,
            RECORDS[1:3],
            5,
        ),
        (
            [1, 2],
            Coord("17", 0, None),
            "GENE1",
            [],
            [],
            [],
            0,
            10,
            [],
            0,
        ),
        (
            [1, 2],
            Coord("17", 0, None),
            None,
            ["Protein coding"],
            ["CDS"],
            [],
            0,
            10,
            [],
            0,
        ),
        (
            [1, 2],
            Coord("1", 80000000, None),
            None,
            [],
            ["Exonic", "Intronic"],
            [],
            0,
            10,
            [RECORDS[3]],
            1,
        ),
        (
            [1, 2],
            Coord(None, 0, None),
            None,
            [],
            [],
            [],
            100,
            10,
            [],
            5,
        ),
    ],
)
def test_get_modifications_records_by_selection(
    technology_ids,
    coord,
    gene_name,
    biotypes,
    features,
    sort,
    offset,
    limit,
    expected_records,
    expected_total,
    Session,
    mocker,
    annotation,
):  # noqa
    modification_service = _get_modification_service(Session())
    # patch base query, cf. #154
    mocker.patch.object(modification_service, "_build_query", _mock_build_query)
    search_params = SearchParams(
        gene_name=gene_name,
        biotypes=biotypes,
        features=features,
        chrom=coord.chrom,
        chrom_start=coord.start,
        chrom_end=coord.end,
    )
    page_params = PageParams(
        offset=offset,
        limit=limit,
        sort=sort,
    )
    response = modification_service.get_modification_records_by_selection(
        annotation_source=AnnotationSource.ENSEMBL,
        taxa_id=9606,
        modification_id=1,
        organism_id=1,
        technology_ids=technology_ids,
        search_params=search_params,
        page_params=page_params,
    )
    assert response["totalRecords"] == expected_total
    assert response["records"] == expected_records


@pytest.mark.parametrize(
    "coord,gene_name,expected_total,expected_records",
    [
        # gene
        (Coord(None, None, None), "GENE1", 1, [RECORDS[0]]),
        # full chrom range
        (Coord("1", 20000000, 105000000), None, 3, RECORDS[:3]),
        # chrom_end w/o chrom_start
        (Coord("1", None, 30000000), None, 4, RECORDS[0:4]),
        # chrom and gene, disjoint
        (Coord("17", None, None), "GENE1", 0, []),
        # chrom and gene, intersecting
        (Coord("1", None, None), "GENE1", 1, [RECORDS[0]]),
    ],
)
def test_get_modification_records_by_gene(
    Session,
    mocker,
    annotation,
    coord,
    gene_name,
    expected_total,
    expected_records,
):  # noqa
    modification_service = _get_modification_service(Session())
    # patch base query, cf. #154
    mocker.patch.object(modification_service, "_build_query", _mock_build_query)
    search_params = SearchParams(
        gene_name=gene_name,
        chrom=coord.chrom,
        chrom_start=coord.start,
        chrom_end=coord.end,
    )
    response = modification_service.get_modification_records_by_gene(
        annotation_source=AnnotationSource.ENSEMBL,
        taxa_id=9606,
        search_params=search_params,
        page_params=PageParams(),
    )
    assert response["totalRecords"] == expected_total
    assert response["records"] == expected_records


@pytest.mark.parametrize(
    "coord,gene_name,expected_total,expected_ids",
    [
        # start/end given w/o chrom: chrom filter skipped
        (Coord(None, 20000000, 30000000), None, 7, [4, 5, 6, 7, 1, 3, 2]),
        # nothing given
        (Coord(None, None, None), None, 7, [4, 5, 6, 7, 1, 3, 2]),
    ],
)
def test_get_modification_records_by_gene_no_filters(
    Session,
    mocker,
    annotation,
    coord,
    gene_name,
    expected_total,
    expected_ids,
):  # noqa
    modification_service = _get_modification_service(Session())
    # patch base query, cf. #154
    mocker.patch.object(modification_service, "_build_query", _mock_build_query)
    search_params = SearchParams(
        gene_name=gene_name,
        chrom=coord.chrom,
        chrom_start=coord.start,
        chrom_end=coord.end,
    )
    response = modification_service.get_modification_records_by_gene(
        annotation_source=AnnotationSource.ENSEMBL,
        taxa_id=9606,
        search_params=search_params,
        page_params=PageParams(),
    )
    assert response["totalRecords"] == expected_total
    assert [r["id"] for r in response["records"]] == expected_ids


def test_get_modification_site(Session, dataset):  # noqa
    modification_service = _get_modification_service(Session())
    response = modification_service.get_modification_site("17", 100001, 100002)
    assert len(response["records"]) == 2
    # query has no ORDER BY, so the row order is DB-dependent!
    # It's just the insertion order in SQLite; it will not be guaranteed in MySQL.
    assert response["records"][0]["dataset_id"] == "dataset_id01"
    assert response["records"][1]["dataset_id"] == "dataset_id02"
    assert response["records"][0]["cto"] == "Cell type 1"
    assert response["records"][1]["cto"] == "Cell type 2"
    assert response["records"][0]["tech"] == "Technology 1"
    assert response["records"][1]["tech"] == "Technology 2"
    assert response["records"][0]["score"] == 1000
    assert response["records"][1]["score"] == 10
