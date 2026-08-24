from io import StringIO
from typing import Any, Iterable, Sequence
from csv import DictReader

import pytest
from flask import Flask

from scimodom.api.modification import (
    modification_api,
    IntersectResponse,
)
from scimodom.utils.dtos.bedtools import Bed6Record
from scimodom.utils.specs.enums import (
    Strand,
    TargetsFileType,
    AnnotationSource,
)


@pytest.fixture
def test_client():
    app = Flask(__name__)
    app.register_blueprint(modification_api, url_prefix="")
    yield app.test_client()


@pytest.fixture
def mock_services(mocker):
    mocker.patch(
        "scimodom.api.modification.get_file_service",
        return_value=MockFileService(),
    )
    mocker.patch(
        "scimodom.api.modification.get_bedtools_service",
        return_value=MockBedtoolsService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_utilities_service",
        return_value=MockUtilitiesService(),
    )
    mocker.patch(
        "scimodom.api.helpers.get_assembly_service",
        return_value=MockAssemblyService(),
    )
    mocker.patch(
        "scimodom.api.modification.get_modification_service",
        return_value=MockModificationService(),
    )


class MockAssemblyService:
    VALID_TAXA = [9606, 10090, 7227]

    @staticmethod
    def get_chroms(taxa_id: int) -> list[dict[str, Any]]:
        if taxa_id in MockAssemblyService.VALID_TAXA:
            return [
                {"chrom": "1", "size": 248956422},
                {"chrom": "17", "size": 83257441},
            ]
        else:
            raise FileNotFoundError


class MockUtilitiesService:
    @staticmethod
    def get_taxa() -> list[dict[str, Any]]:
        return [
            {
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Chordata",
            },
            {
                "taxa_id": 10090,
                "taxa_name": "Mus musculus",
                "taxa_sname": "M. musculus",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Chordata",
            },
            {
                "taxa_id": 7227,
                "taxa_name": "Drosophila melanogaster",
                "taxa_sname": "D. melanogaster",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "phylum": "Arthropoda",
            },
        ]

    @staticmethod
    def get_rna_types() -> list[dict[str, Any]]:
        return [{"id": "WTS", "label": "whole transcriptome"}]


class MockFileService:
    VALID_TAXA = [9606, 10090]
    FILE_CONTENT = {
        TargetsFileType.MIRNA: "1\t3284722\t3284729\tTargetScan:Target:miR\t75\t+",
        TargetsFileType.RBP: "1\t2403126\t2403133\toRNAment:Target:1:Motif\t750\t+",
    }

    @staticmethod
    def open_file_for_reading(path):  # noqa
        return StringIO("")

    @staticmethod
    def open_annotation_targets_file(
        taxa_id: int, target_type: TargetsFileType, chrom: str
    ):  # noqa
        if taxa_id in MockFileService.VALID_TAXA and isinstance(
            target_type, TargetsFileType
        ):
            return StringIO(MockFileService.FILE_CONTENT[target_type])
        else:
            raise FileNotFoundError


class MockBedtoolsService:
    RECORDS = [
        Bed6Record(
            chrom="1",
            start=3284722,
            end=3284729,
            name="TargetScan:Target:miR",
            score=75,
            strand=Strand.FORWARD,
        ),
        Bed6Record(
            chrom="1",
            start=2403126,
            end=2403133,
            name="oRNAment:Target:1:Motif",
            score=750,
            strand=Strand.FORWARD,
        ),
    ]

    @staticmethod
    def create_temp_file_from_records(
        records: Iterable[Sequence[Any]], sort: bool = True
    ) -> str:  # noqa
        MockBedtoolsService.INTERSECTION_RECORDS = []
        return "/tmp/pybedtools.tmp"

    @staticmethod
    def intersect_bed6_records(
        a_records: Iterable[Bed6Record],
        b_stream: StringIO,
        is_strand: bool,
        is_sorted: bool = True,
    ) -> Iterable[Bed6Record]:  # noqa
        line = b_stream.getvalue()
        if "TargetScan" in line:
            MockBedtoolsService.INTERSECTION_RECORDS = [MockBedtoolsService.RECORDS[0]]
        else:
            MockBedtoolsService.INTERSECTION_RECORDS = [MockBedtoolsService.RECORDS[1]]
        return MockBedtoolsService.INTERSECTION_RECORDS


class MockModificationService:
    RECORDS = [
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
    ]

    @staticmethod
    def get_modifications_by_source(
        annotation_source: AnnotationSource,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        return {
            "totalRecords": 1,
            "records": [MockModificationService.RECORDS[0].copy()],
        }

    @staticmethod
    def get_modifications_by_gene(
        annotation_source: AnnotationSource,
        taxa_id: int,
        gene_filter: list[str],
        chrom: str | None,
        chrom_start: int | None,
        chrom_end: int | None,
        first_record: int | None,
        max_records: int | None,
        multi_sort: list[str],
    ) -> dict[str, Any]:
        return {
            "totalRecords": 1,
            "records": [MockModificationService.RECORDS[1].copy()],
        }


# TODO
# returns a response in the test, but the API returns an empty response:
# a random/inexistent modification, as long as it is a valid int
# a random/inexistent organism, as long as it is a valid int
# malformed technology, invalid value, random/inexistent value
# malformed or invalid value (str instead of int) for firstRecord, maxRecords
# malformed geneFilter, incl. gene_name, missing components (startsWith, in, etc. FAIL in production),
# gene_biotypes, malformed or inexistent features or biotypes
# both geneFilter (gene_name) and chrom
# malformed chrom, start and end, random chrom (any string, negative value), range for start/end
@pytest.mark.parametrize(
    "url",
    [
        "query?modification=99999&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=11111&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technologi[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=a&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1288888&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstrecord=0&maximumRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=a&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&gene_filter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feat%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA&geneFilter[]=feat%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2Bwhatever%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BABC%2Bin&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&chrom=1&chromStart=1&chromEnd=10000&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&Chrom=1&chromStart=1&chromEnd=10000&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&chrom=a&chromStart=1&chromEnd=10000&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&chrom=-1&chromStart=1&chromEnd=10000&firstRecord=0&maxRecords=1",
        "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&chrom=1&chromStart=12&chromEnd=1&firstRecord=0&maxRecords=1",
    ],
)
def test_get_modification_as_json_success(test_client, mock_services, url):
    result = test_client.get(url)
    expected_records = [
        {**r, "strand": r["strand"].value} for r in MockModificationService.RECORDS
    ]
    assert result.status_code == 200
    assert result.json["records"][0] == expected_records[0]


# TODO
# returns a response in the test, but the API returns an empty response:
# if one geneFilter (no matter which one, no matter if content is bad) and chrom missing or malformed
# wrong range - also tested elsewhere
@pytest.mark.parametrize(
    "url",
    [
        "query/gene?rnaType=WTS&taxaId=9606&genefilter[]=genebiotype%2BProtein+coding%2Bin&geneFilter[]=feat%2BCDS%2Bin&xhrom=7&chromStart=5527750&chromEnd=5527760&firstRecord=0&maxRecords=10",
        "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=50&chromEnd=1&firstRecord=0&maxRecords=10",
    ],
)
def test_get_modification_as_json_by_gene_success(test_client, mock_services, url):
    result = test_client.get(url)
    expected_records = [
        {**r, "strand": r["strand"].value} for r in MockModificationService.RECORDS
    ]
    assert result.status_code == 200
    assert result.json["records"][0] == expected_records[1]


# TODO
@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "query?Modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid modification",
        ),
        (
            "query?modification=a&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid modification",
        ),
        (
            "query?modification=1&organ=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid organism",
        ),
        (
            "query?modification=1&organism=-1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid organism",
        ),
        (
            "query?modification=1&organism=1&technology[]=1&rnaType=wts&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            404,
            "Unknown RNA type",
        ),
        (
            "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=a&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid Taxa ID",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&genefilter[]=gene_name%2BGENE%2BstartsWith&&Chrom=1&chromStart=0&chromEnd=10000&firstRecord=0&maxRecords=10",
            400,
            "Gene or chromosome is required",
        ),
    ],
)
def test_get_modification_as_json_extra(
    test_client, mock_services, url, http_status, message
):
    result = test_client.get(url)
    assert result.status_code == http_status
    assert result.json["message"] == message


@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "query?modification=1&organism=1&technology[]=1&rnatype=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            404,
            "Unknown RNA type",
        ),
        (
            "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid Taxa ID",
        ),
        (
            "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=960&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            404,
            "Unrecognized Taxa ID",
        ),
        (
            "query?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=-1&maxRecords=1",
            400,
            "Invalid firstRecord",
        ),
        (
            "query?modification=1&organism=1&technology[]=-1&rnaType=WTS&taxaId=9606&geneFilter[]=gene_name%2BGENE%2BstartsWith&geneFilter[]=gene_biotype%2BlncRNA%2Bin&geneFilter[]=feature%2BCDS%2Bin&firstRecord=0&maxRecords=1",
            400,
            "Invalid technology ID",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=-1&chromEnd=10000&firstRecord=0&maxRecords=10",
            400,
            "Invalid chromStart",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromEnd=10000&firstRecord=0&maxRecords=10",
            400,
            "Invalid chromStart",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=1&chromEnd=0&firstRecord=0&maxRecords=10",
            400,
            "Invalid chromEnd",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chromStart=0&chromEnd=10000&firstRecord=0&maxRecords=10",
            400,
            "Gene or chromosome is required",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=1&chromEnd=10000&multiSort[]=star%2Basc&firstRecord=0&maxRecords=10",
            400,
            "Invalid table sort (multiSort) field",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=1&chromEnd=10000&multiSort[]=start%2Bascending&firstRecord=0&maxRecords=10",
            400,
            "Invalid table sort (multiSort) direction",
        ),
    ],
)
def test_get_modification_as_json(
    test_client, mock_services, url, http_status, message
):
    result = test_client.get(url)
    assert result.status_code == http_status
    assert result.json["message"] == message


@pytest.mark.freeze_time("2026-08-24 20:00:00")
def test_get_modification_as_csv(test_client, mock_services):
    url = "csv?modification=1&organism=1&technology[]=1&rnaType=WTS&taxaId=9606"
    response = test_client.get(url)
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="scimodom_search_2026-08-24T200000.csv"'
    )
    reader = DictReader(StringIO(response.text))
    assert list(reader) == [
        {
            "chrom": "17",
            "chromStart": "100001",
            "chromEnd": "100002",
            "name": "m6A",
            "score": "1000",
            "strand": "+",
            "coverage": "43",
            "frequency": "100",
            "EUFID": "dataset_id01",
            "Technology": "Technology 1",
            "Organism": "9606",
            "Cell/Tissue": "Cell type 1",
            "Feature": "",
            "Gene": "",
            "Biotype": "",
        }
    ]


# https://scimodom-beta.dieterichlab.org/api/v0/modification/sitewise?chrom=1&start=944239&end=944240&strand=-&taxaId=9606
# strand can be missing
# prod: the whole selection is passed through, with taxa_id


@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "/target/MIRNAs?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=%2B",
            404,
            "Unknown targets type",
        ),
        (
            "/target/MIRNA?taxaId=9605&chrom=1&start=3284723&end=3284724&strand=%2D",
            404,
            "Unrecognized Taxa ID",
        ),
        (
            "/target/MIRNA?taxaId=a&chrom=1&start=3284723&end=3284724&strand=%2E",
            400,
            "Invalid Taxa ID",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=I&start=3284723&end=3284724&strand=%2B",
            404,
            "Unrecognized chrom 'I' for Taxa '9606'",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284721&end=end&strand=%2B",
            400,
            "Invalid end",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=start&end=3284722&strand=%2B",
            400,
            "Invalid start",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284722&strand=%2B",
            400,
            "Invalid coordinates: start must be smaller than end",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=248956422&strand=%2B",
            400,
            "Invalid coordinates: end is greater than chrom size",
        ),
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=+",
            400,
            "Invalid strand value",
        ),
    ],
)
def test_get_modification_targets_bad_url(
    test_client, mock_services, url, http_status, message
):
    result = test_client.get(url)
    assert result.status_code == http_status
    assert result.json["message"] == message


@pytest.mark.parametrize(
    "url",
    [
        "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=%2B",
        "/target/RBP?taxaId=9606&chrom=1&start=2403131&end=2403132&strand=%2B",
    ],
)
def test_get_modification_targets(test_client, mock_services, url):
    result = test_client.get(url)
    assert result.status == "200 OK"
    assert (
        IntersectResponse.model_validate_json(result.text).records
        == MockBedtoolsService.INTERSECTION_RECORDS
    )


def test_get_modification_targets_empty(test_client, mock_services, caplog):
    url = "/target/MIRNA?taxaId=7227&chrom=1&start=3284723&end=3284724&strand=%2B"
    result = test_client.get(url)
    assert result.status == "200 OK"
    assert (
        IntersectResponse.model_validate_json(result.text).records
        == MockBedtoolsService.INTERSECTION_RECORDS
    )
    assert caplog.record_tuples == [
        (
            "scimodom.api.modification",
            30,
            "API not implemented for Taxa ID '7227': silently returning empty response!",
        )
    ]
