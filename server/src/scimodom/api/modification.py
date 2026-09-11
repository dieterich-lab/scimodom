from csv import DictWriter
from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable, TextIO

from flask import Blueprint, Response
from flask_cors import cross_origin
from pydantic import BaseModel

from scimodom.services.annotation import AnnotationService
from scimodom.services.modification import (
    MultiSortError,
    get_modification_service,
)
from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    get_optional_query_param,
    get_route_param,
    get_positive_int,
    get_non_negative_int,
    get_optional_positive_int,
    get_optional_non_negative_int,
    validate_chrom,
    get_valid_rna_type,
    get_valid_biotypes,
    get_valid_features,
    get_valid_taxa_id,
    get_valid_coords,
    get_valid_target_type,
    get_valid_selections,
    get_response_from_pydantic_object,
    get_unique_list_from_query_param,
)
from scimodom.services.bedtools import BedToolsService, get_bedtools_service
from scimodom.utils.dtos.bedtools import Bed6Record
from scimodom.services.file import get_file_service
from scimodom.utils.specs.enums import (
    Strand,
    AssemblyFileType,
)

logger = logging.getLogger(__name__)

modification_api = Blueprint("modification_api", __name__)

FIELDS_TO_CSV_HEADER_MAP = {
    "chrom": "chrom",
    "start": "chromStart",
    "end": "chromEnd",
    "name": "name",
    "score": "score",
    "strand": "strand",
    "coverage": "coverage",
    "frequency": "frequency",
    "dataset_id": "EUFID",
    "tech": "Technology",
    "taxa_id": "Organism",
    "cto": "Cell/Tissue",
    "feature": "Feature",
    "gene_name": "Gene",
    "gene_biotype": "Biotype",
}


@dataclass
class SearchQueryParams:
    """DTO for Search query parameters."""

    gene_name: str | None
    biotypes: list[str]
    features: list[str]
    chrom: str | None = None
    chrom_start: int | None = None
    chrom_end: int | None = None


class IntersectResponse(BaseModel):
    """DTO for BED6 records."""

    records: list[Bed6Record]


@modification_api.route("/query", defaults={"by_gene": None}, methods=["GET"])
@modification_api.route("/query/<by_gene>")
@cross_origin(supports_credentials=True)
def get_modifications_as_json(by_gene):
    """Query modifications.

    :param request: The request with search parameters.
    :param by_gene: Query by gene (default: by modification)
    :return: JSON array with all modifications satisfying the
    query criteria, incl. selected bedRMod fields, annotations,
    and DB-associated IDs.
    :statuscode 200: OK
    :statuscode 400: Bad request (syntax validation failed,
    structurally invalid request)
    :statuscode 404: Not found (semantic validation failed,
    database entity or resource does not exist)
    :statuscode 422: Unprocessable Content (API constraints
    failed e.g. range constraints, enum-allowed values, etc.)
    :statuscode 500: Internal Server Error
    :statuscode 501: Not Implemented (TODO MS14)
    """
    try:
        records = _get_modifications_for_request(by_gene)
    except ClientResponseException as exc:
        return exc.response_tuple
    records["records"] = [
        {**r, "strand": r["strand"].value} for r in records["records"]
    ]
    return records


@modification_api.route("/csv", defaults={"by_gene": None}, methods=["GET"])
@modification_api.route("/csv/<by_gene>")
@cross_origin(supports_credentials=True)
def get_modifications_as_csv(by_gene):
    """Query modifications and return a CSV.

    :param request: The request with search parameters.
    :param by_gene: Query by gene (default: by modification)
    :return: A CSV with all modifications satisfying the
    query criteria, incl. selected bedRMod fields, annotations,
    and DB-associated IDs. Records field names are mapped with
    FIELDS_TO_CSV_HEADER_MAP.
    :statuscode 200: OK
    :statuscode 400: Bad request (syntax validation failed,
    structurally invalid request)
    :statuscode 404: Not found (semantic validation failed,
    database entity or resource does not exist)
    :statuscode 422: Unprocessable Content (API constraints
    failed e.g. range constraints, enum-allowed values, etc.)
    :statuscode 500: Internal Server Error
    :statuscode 501: Not Implemented (TODO MS14)
    """
    try:
        records = _get_modifications_for_request(by_gene)
    except ClientResponseException as exc:
        return exc.response_tuple
    records_as_csv = _get_csv_from_modifications_records(records["records"])
    now = datetime.now(timezone.utc)
    file_name = now.strftime("scimodom_search_%Y-%m-%dT%H%M%S.csv")
    return Response(
        response=records_as_csv,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
    )


@modification_api.route("/sitewise", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification_sitewise():
    """Get information related to a modification site.

    :param request: The request with search parameters.
    :return: JSON object with all metadata associated with
    a modification site.
    :statuscode 200: OK
    :statuscode 400: Bad request (syntax validation failed,
    structurally invalid request)
    :statuscode 404: Not found (semantic validation failed,
    database entity or resource does not exist)
    :statuscode 422: Unprocessable Content (API constraints
    failed e.g. range constraints, enum-allowed values, etc.)
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_valid_taxa_id()
        chrom, start, end, _ = get_valid_coords(taxa_id)
    except ClientResponseException as exc:
        return exc.response_tuple

    modification_service = get_modification_service()
    records = modification_service.get_modification_site(chrom, start, end)
    records["records"] = [
        {**r, "strand": r["strand"].value} for r in records["records"]
    ]
    return records


@modification_api.route("/genomic-context/<context>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genomic_sequence_context(context):
    """Get sequence context for a modification site.

    :param request: The request with search parameters.
    :param context: The genomic context around a site
    :return: JSON object with sequence context around a
    modification site.
    :statuscode 200: OK
    :statuscode 400: Bad request (syntax validation failed,
    structurally invalid request)
    :statuscode 404: Not found (semantic validation failed,
    database entity or resource does not exist)
    :statuscode 422: Unprocessable Content (API constraints
    failed e.g. range constraints, enum-allowed values, etc.)
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_valid_taxa_id()
        context_as_int = get_route_param(
            "context",
            context,
            "non_negative_int",
        )
        coords = get_valid_coords(taxa_id, context=context_as_int)
    except ClientResponseException as exc:
        return exc.response_tuple

    bedtools_service = get_bedtools_service()
    file_service = get_file_service()

    try:
        fasta_file = file_service.get_assembly_file_path(
            taxa_id, file_type=AssemblyFileType.DNA, chrom=coords[0]
        )
        records = _get_bed6_records_from_request(coords)
        seq_file = bedtools_service.getfasta(records, fasta_file, is_strand=True)
        sequence = file_service.read_sequence_context(seq_file)
    except FileNotFoundError:
        logger.warning(
            f"API not implemented for Taxa ID '{taxa_id}': silently returning empty context!"
        )
        sequence = ""
    return {"context": sequence}


@modification_api.route("/target/<target_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification_targets(target_type):
    """Get miRNA targets and RBP binding sites affected by a modification.

    :param request: The request with search parameters.
    :param target_type: The allowed target type e.g. MIRNA, RBP
    :return: JSON array with site table information for selected target.
    :statuscode 200: OK
    :statuscode 400: Bad request (syntax validation failed,
    structurally invalid request)
    :statuscode 404: Not found (semantic validation failed,
    database entity or resource does not exist)
    :statuscode 422: Unprocessable Content (API constraints
    failed e.g. range constraints, enum-allowed values, etc.)
    :statuscode 500: Internal Server Error
    """
    try:
        with _ModificationContext(target_type) as ctx:
            records = ctx.bedtools_service.intersect_bed6_records(
                ctx.records, ctx.stream, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(IntersectResponse(records=records))
    except ClientResponseException as exc:
        return exc.response_tuple


class _ModificationContext:
    @dataclass
    class Ctx:
        bedtools_service: BedToolsService
        records: Iterable[Bed6Record]
        is_strand: bool
        stream: TextIO

    def __init__(self, target_type: str):
        self._target_type = get_valid_target_type(target_type)
        self._is_strand = True
        self._taxa_id = get_valid_taxa_id()
        self._coords = get_valid_coords(self._taxa_id)

    def __enter__(self) -> Ctx:
        file_service = get_file_service()
        bedtools_service = get_bedtools_service()
        try:
            self._annotation_targets_file = file_service.open_annotation_targets_file(
                self._taxa_id, self._target_type, chrom=self._coords[0]
            )
        except FileNotFoundError:
            logger.warning(
                f"API not implemented for Taxa ID '{self._taxa_id}': silently returning empty response!"
            )
            temp_file = bedtools_service.create_temp_file_from_records([], sort=False)
            self._annotation_targets_file = file_service.open_file_for_reading(
                temp_file
            )

        records = _get_bed6_records_from_request(self._coords)

        return self.Ctx(
            bedtools_service=bedtools_service,
            records=records,
            stream=self._annotation_targets_file,
            is_strand=self._is_strand,
        )

    def __exit__(self, exc_type, exc_value, traceback):
        self._annotation_targets_file.close()


def _get_bed6_records_from_request(
    coords: tuple[str, int, int, Strand]
) -> Iterable[Bed6Record]:
    return [
        Bed6Record(
            chrom=coords[0],
            start=coords[1],
            end=coords[2],
            name="-",
            score=0,
            strand=coords[3],
        )
    ]


def _get_modifications_for_request(by_gene):
    modification_service = get_modification_service()

    rna_type = get_valid_rna_type()
    taxa_id = get_valid_taxa_id()

    # TODO MS14
    try:
        annotation_source = AnnotationService.get_annotation_source(rna_type)
    except NotImplementedError:
        raise ClientResponseException(501, f"rnaType '{rna_type}' not implemented")

    search_query_params = _get_valid_search_query_params(taxa_id, by_gene)
    multi_sort = get_unique_list_from_query_param("multiSort", str)
    multi_sort = list(filter(None, multi_sort))
    if not multi_sort:
        multi_sort = ["chrom+asc", "start+asc"]
    first_record = get_optional_non_negative_int("firstRecord")
    max_records = get_optional_positive_int("maxRecords")

    try:
        if by_gene:
            return modification_service.get_modifications_by_gene(
                annotation_source=annotation_source,
                taxa_id=taxa_id,
                gene_name=search_query_params.gene_name,
                biotypes=search_query_params.biotypes,
                features=search_query_params.features,
                chrom=search_query_params.chrom,
                chrom_start=search_query_params.chrom_start,
                chrom_end=search_query_params.chrom_end,
                first_record=first_record,
                max_records=max_records,
                multi_sort=multi_sort,
            )
        else:
            modification_id, organism_id, technology_ids = get_valid_selections()
            return modification_service.get_modifications_by_source(
                annotation_source=annotation_source,
                modification_id=modification_id,
                organism_id=organism_id,
                technology_ids=technology_ids,
                taxa_id=taxa_id,
                gene_name=search_query_params.gene_name,
                biotypes=search_query_params.biotypes,
                features=search_query_params.features,
                chrom=search_query_params.chrom,
                chrom_start=search_query_params.chrom_start,
                chrom_end=search_query_params.chrom_end,
                first_record=first_record,
                max_records=max_records,
                multi_sort=multi_sort,
            )
    except MultiSortError as exc:
        raise ClientResponseException(400, f"{exc}")


def _get_csv_from_modifications_records(records):
    as_text = StringIO()
    writer = DictWriter(
        as_text, fieldnames=FIELDS_TO_CSV_HEADER_MAP.values(), dialect="excel"
    )
    writer.writeheader()
    for raw in records:
        cooked = {v: raw[k] for k, v in FIELDS_TO_CSV_HEADER_MAP.items()}
        cooked["strand"] = cooked["strand"].value
        writer.writerow(cooked)
    return as_text.getvalue()


def _get_valid_search_query_params(
    taxa_id: int,
    by_gene: bool,
) -> SearchQueryParams:
    gene_name = get_optional_query_param("geneName")
    chrom = get_optional_query_param("chrom")
    chrom_start = get_optional_non_negative_int("chromStart")
    chrom_end = get_optional_positive_int("chromEnd")
    if (chrom_start or chrom_end) and not chrom:
        raise ClientResponseException(
            400,
            "Unused parameters: 'chromStart' and 'chromEnd' require 'chrom'",
        )
    if chrom_end and not chrom_start:
        raise ClientResponseException(
            400,
            "Unused parameters: 'chromEnd' require 'chromStart'",
        )
    if gene_name and chrom:
        raise ClientResponseException(
            400,
            "Too many parameters: use 'geneName' xor 'chrom'",
        )
    if by_gene:
        if not gene_name and not chrom:
            raise ClientResponseException(
                400,
                "Missing required parameter: 'geneName' xor 'chrom'",
            )
        if chrom:
            chrom_start = get_non_negative_int("chromStart")
            chrom_end = get_positive_int("chromEnd")
    if chrom:
        validate_chrom(taxa_id, chrom, chrom_start, chrom_end)
    biotypes = get_valid_biotypes()
    features = get_valid_features()
    return SearchQueryParams(
        gene_name, biotypes, features, chrom, chrom_start, chrom_end
    )
