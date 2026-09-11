from io import StringIO
from pathlib import Path
from typing import Any, Iterable, Sequence
from csv import DictReader

import pytest
from flask import Flask

from scimodom.api.modification import (
    modification_api,
    IntersectResponse,
)
from scimodom.services.modification import MultiSortError
from scimodom.utils.dtos.bedtools import Bed6Record
from scimodom.utils.specs.enums import (
    Strand,
    TargetsFileType,
    AnnotationSource,
    AssemblyFileType,
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
        "scimodom.api.helpers.get_annotation_service",
        return_value=MockAnnotationService(),
    )
    mocker.patch(
        "scimodom.api.modification.get_modification_service",
        return_value=MockModificationService(),
    )


class MockAnnotationService:
    VALID_RNA_TYPES = ["WTS"]

    @staticmethod
    def get_features_by_rna_type(rna_type: str):
        if rna_type not in MockAnnotationService.VALID_RNA_TYPES:
            raise NotImplementedError
        return ["CDS", "exon", "intron"]


class MockAssemblyService:
    VALID_TAXA = [9606, 10090, 7227]

    @staticmethod
    def get_chroms(taxa_id: int) -> list[dict[str, str | int]]:
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
        return [
            {"id": "WTS", "label": "whole transcriptome"},
            {"id": "WTS2", "label": "whole transcriptome2"},
        ]

    @staticmethod
    def get_biotypes():
        return {"biotypes": ["Protein coding", "lncRNA"]}

    @staticmethod
    def get_selections():
        return [
            {
                "cls": "NGS 2nd generation",
                "cto": "HeLa",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "meth": "Chemical-assisted sequencing",
                "modification_id": 2,
                "modomics_sname": "m6A",
                "organism_id": 3,
                "rna": "WTS",
                "rna_name": "whole transcriptome",
                "selection_id": 3,
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "tech": "MePMe-seq",
                "technology_id": 2,
            },
            {
                "cls": "NGS 2nd generation",
                "cto": "HeLa",
                "domain": "Eukarya",
                "kingdom": "Animalia",
                "meth": "Enzyme/protein-assisted sequencing",
                "modification_id": 2,
                "modomics_sname": "m6A",
                "organism_id": 3,
                "rna": "WTS",
                "rna_name": "whole transcriptome",
                "selection_id": 29,
                "taxa_id": 9606,
                "taxa_name": "Homo sapiens",
                "taxa_sname": "H. sapiens",
                "tech": "eTAM-seq",
                "technology_id": 7,
            },
        ]


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

    @staticmethod
    def get_assembly_file_path(
        taxa_id: int,
        file_type: AssemblyFileType,
        assembly_name: str | None = None,
        chrom: str | None = None,
    ) -> Path:
        return Path("path")

    @staticmethod
    def read_sequence_context(fasta_file: str) -> str:
        return "ACGTAACCGCC"


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

    @staticmethod
    def getfasta(
        records: Iterable[Bed6Record], fasta_file: Path, is_strand: bool
    ) -> str:
        return "fasta_file"


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
    SITEWISE_RECORDS = [
        {
            "chrom": "1",
            "coverage": 53,
            "cto": "HeLa",
            "dataset_id": "bLzgK48AVvYg",
            "end": 944240,
            "frequency": 16,
            "modification_id": 5,
            "name": "Am",
            "reference_id": 127,
            "rna": "WTS",
            "score": 0,
            "short_name": "H. sapiens",
            "start": 944239,
            "strand": Strand.REVERSE,
            "tech": "NanoNm",
        },
        {
            "chrom": "1",
            "coverage": 20,
            "cto": "C4-2",
            "dataset_id": "Qjh5Y6qXGAFD",
            "end": 944240,
            "frequency": 30,
            "modification_id": 5,
            "name": "Am",
            "reference_id": 127,
            "rna": "WTS",
            "score": 0,
            "short_name": "H. sapiens",
            "start": 944239,
            "strand": Strand.REVERSE,
            "tech": "NanoNm",
        },
    ]

    @staticmethod
    def get_modifications_by_source(
        annotation_source: AnnotationSource,
        modification_id: int,
        organism_id: int,
        technology_ids: list[int],
        taxa_id: int,
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
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
        gene_name: str | None,
        biotypes: list[str],
        features: list[str],
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

    @staticmethod
    def get_modification_site(
        chrom: str,
        start: int,
        end: int,
    ) -> dict[str, list[str, Any]]:
        return {"records": MockModificationService.SITEWISE_RECORDS.copy()}


# tests


@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS2&taxaId=9606",
            501,
            "rnaType 'WTS2' not implemented",
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606&geneName=GENE&chromStart=1",
            400,
            "Unused parameters: 'chromStart' and 'chromEnd' require 'chrom'",
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606&chrom=ANY&chromEnd=1",
            400,
            "Unused parameters: 'chromEnd' require 'chromStart'",
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606&geneName=GENE&chrom=ANY",
            400,
            "Too many parameters: use 'geneName' xor 'chrom'",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606",
            400,
            "Missing required parameter: 'geneName' xor 'chrom'",
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606",
            200,
            None,
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=2",
            400,
            "Missing required parameter: 'chromEnd'",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=2&chromEnd=a",
            400,
            "Parameter 'chromEnd' must be a valid integer (got: 'a')",
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606&chrom=1&chromStart=2",
            200,
            None,
        ),
        (
            "query?modification=2&organism=3&technology=2&rnaType=WTS&taxaId=9606&firstRecord=first",
            400,
            "Parameter 'firstRecord' must be a valid integer (got: 'first')",
        ),
    ],
)
def test_get_modification_as_json(
    test_client, mock_services, url, http_status, message
):
    result = test_client.get(url)
    assert result.status_code == http_status
    if message is not None:
        assert result.json["message"] == message


@pytest.mark.parametrize(
    "url,func",
    [
        (
            "query?modification=2&organism=3&technology[]=2&rnaType=WTS&taxaId=9606",
            "get_modifications_by_source",
        ),
        (
            "query/gene?rnaType=WTS&taxaId=9606&chrom=1&chromStart=1&chromEnd=10000",
            "get_modifications_by_gene",
        ),
    ],
)
def test_multisort_fail(test_client, mock_services, mocker, url, func):
    mocker.patch.object(
        MockModificationService,
        func,
        side_effect=MultiSortError("mock exception"),
    )

    response = test_client.get(url)
    assert response.status_code == 400
    assert response.json == {"message": "mock exception"}


@pytest.mark.freeze_time("2026-08-24 20:00:00")
def test_get_modification_as_csv(test_client, mock_services):
    url = "csv?modification=2&organism=3&technology[]=2&rnaType=WTS&taxaId=9606"
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


def test_get_modification_sitewise(test_client, mock_services):
    url = "sitewise?chrom=1&start=944239&end=944240&strand=-&taxaId=9606"
    response = test_client.get(url)
    expected_records = [
        {**r, "strand": r["strand"].value}
        for r in MockModificationService.SITEWISE_RECORDS
    ]
    assert response.status_code == 200
    assert response.json["records"] == expected_records


def test_get_genomic_sequence_context(test_client, mock_services):
    response = test_client.get(
        "genomic-context/1?chrom=1&end=944240&start=944239&strand=-&taxaId=9606"
    )
    assert response.status_code == 200
    assert response.json == {"context": "ACGTAACCGCC"}


def test_get_genomic_sequence_context_file_not_found(
    test_client, mock_services, mocker, caplog
):
    mocker.patch.object(
        MockBedtoolsService,
        "getfasta",
        side_effect=FileNotFoundError,
    )

    response = test_client.get(
        "genomic-context/5?chrom=1&end=944240&start=944239&strand=-&taxaId=9606"
    )
    assert response.status_code == 200
    assert response.json == {"context": ""}
    assert caplog.messages == [
        "API not implemented for Taxa ID '9606': silently returning empty context!"
    ]


# TODO
# cf. test_get_modification_sitewise with strand=-
@pytest.mark.parametrize(
    "url,http_status,message",
    [
        (
            "/target/MIRNA?taxaId=9606&chrom=1&start=3284723&end=3284724&strand=+",
            422,
            "Parameter 'strand' must be +, -, or .",
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
