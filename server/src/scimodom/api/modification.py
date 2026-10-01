from csv import DictWriter
from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable, TextIO

from flask import Blueprint, Response
from pydantic import BaseModel

from scimodom.services.annotation import AnnotationService
from scimodom.services.modification import (
    MultiSortError,
    get_modification_service,
)
from scimodom.api.helpers import (
    ClientResponseException,
    get_optional_str,
    get_positive_int,
    get_non_negative_int,
    get_optional_positive_int,
    get_optional_non_negative_int,
    validate_chrom,
    get_valid_rna_type,
    get_optional_valid_biotypes,
    get_optional_valid_features,
    get_valid_taxa_id,
    get_valid_coords,
    get_valid_target_type,
    get_valid_selections,
    get_response_from_pydantic_object,
    get_optional_list,
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


@modification_api.get("/records")
def get_modification_records():
    """Get modifications (data records).

    :param request: The request with search parameters.
    :return: JSON array with modifications incl. selected
    bedRMod fields (data), annotation, etc.
    :statuscode 200: OK
    :statuscode 400: Bad request - invalid request, syntax
    :statuscode 404: Not found - semantic validation
    :statuscode 500: Internal Server Error
    :statuscode 501: Not Implemented (TODO MS14)
    """
    try:
        by_gene = get_optional_str("by") == "gene"
        records = _get_modification_records(by_gene)
    except ClientResponseException as exc:
        return exc.response_tuple

    if get_optional_str("format") == "csv":
        records_as_csv = _get_csv_from_modification_records(records["records"])
        now = datetime.now(timezone.utc)
        file_name = now.strftime("scimodom_search_%Y-%m-%dT%H%M%S.csv")
        return Response(
            response=records_as_csv,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )

    records["records"] = [
        {**r, "strand": r["strand"].value} for r in records["records"]
    ]
    return records


@modification_api.get("/sites")
def get_modification_sites():
    """Get modifications per site.

    :param request: The request with search parameters.
    :return: JSON object with all metadata associated with
    a modification site.
    :statuscode 200: OK
    :statuscode 400: Bad request - invalid request, syntax
    :statuscode 404: Not found - semantic validation
    :statuscode 500: Internal Server Error
    """
    try:
        chrom, start, end, _ = get_valid_coords()
    except ClientResponseException as exc:
        return exc.response_tuple

    modification_service = get_modification_service()
    records = modification_service.get_modification_site(chrom, start, end)
    records["records"] = [
        {**r, "strand": r["strand"].value} for r in records["records"]
    ]
    return records


@modification_api.get("/sites/context")
def get_modification_site_context():
    """Get sequence context for a modification site.

    :param request: The request with search parameters.
    :statuscode 200: OK
    :statuscode 400: Bad request - invalid request, syntax
    :statuscode 404: Not found - semantic validation
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_valid_taxa_id()
        context = get_non_negative_int("window")
        coords = get_valid_coords(context=context)
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
            f"Not implemented for taxon '{taxa_id}': returning empty context!"
        )
        sequence = ""
    return {"context": sequence}


@modification_api.get("/sites/targets")
def get_modification_targets():
    """Get targets affected by a modification.

    Targets can be e.g. miRNA targets or RBP binding sites

    :param request: The request with search parameters.
    :statuscode 200: OK
    :statuscode 400: Bad request - invalid request, syntax
    :statuscode 404: Not found - semantic validation
    :statuscode 500: Internal Server Error
    """
    try:
        with _ModificationContext() as ctx:
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

    def __init__(self):
        self._target_type = get_valid_target_type()
        self._is_strand = True
        self._taxa_id = get_valid_taxa_id()
        self._coords = get_valid_coords()

    def __enter__(self) -> Ctx:
        file_service = get_file_service()
        bedtools_service = get_bedtools_service()
        try:
            self._annotation_targets_file = file_service.open_annotation_targets_file(
                self._taxa_id, self._target_type, chrom=self._coords[0]
            )
        except FileNotFoundError:
            logger.warning(
                f"Not implemented for taxon '{self._taxa_id}': returning empty response!"
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


def _get_modification_records(by_gene: bool):
    modification_service = get_modification_service()

    rna_type = get_valid_rna_type()
    taxa_id = get_valid_taxa_id()

    # TODO MS14
    try:
        annotation_source = AnnotationService.get_annotation_source(rna_type)
    except NotImplementedError:
        raise ClientResponseException(501, f"rnaType '{rna_type}' not implemented")

    search_query_params = _get_valid_search_query_params(taxa_id, by_gene)
    multi_sort = get_optional_list("multiSort", str)
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
        raise ClientResponseException(400, str(exc))


def _get_csv_from_modification_records(records):
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
    gene_name = get_optional_str("geneName")
    chrom = get_optional_str("chrom")
    chrom_start = get_optional_non_negative_int("chromStart")
    chrom_end = get_optional_positive_int("chromEnd")

    if gene_name is not None and chrom is not None:
        raise ClientResponseException(
            400,
            "Too many parameters: use 'geneName' xor 'chrom'",
        )

    if chrom is None:
        if chrom_start is not None or chrom_end is not None:
            raise ClientResponseException(
                400,
                "Unused parameters: 'chromStart' and 'chromEnd' require 'chrom'",
            )
    else:
        if chrom_end is not None and chrom_start is None:
            raise ClientResponseException(
                400,
                "Unused parameter: 'chromEnd' requires 'chromStart'",
            )
        if by_gene:
            chrom_start = get_non_negative_int("chromStart")
            chrom_end = get_positive_int("chromEnd")

        validate_chrom(taxa_id, chrom, chrom_start, chrom_end)

    if by_gene and gene_name is None and chrom is None:
        raise ClientResponseException(
            400,
            "Missing required parameter: 'geneName' xor 'chrom'",
        )

    return SearchQueryParams(
        gene_name,
        get_optional_valid_biotypes(),
        get_optional_valid_features(),
        chrom,
        chrom_start,
        chrom_end,
    )
