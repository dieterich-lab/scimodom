from csv import DictWriter
from dataclasses import dataclass
import logging
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable, TextIO

from flask import Blueprint, request, Response
from flask_cors import cross_origin
from pydantic import BaseModel

from scimodom.services.annotation import RNA_TYPE_TO_ANNOTATION_SOURCE_MAP
from scimodom.services.modification import get_modification_service
from scimodom.api.helpers import (
    ClientResponseException,
    get_positive_int,
    get_valid_coords,
    get_valid_targets_type,
    get_valid_taxa_id,
    get_response_from_pydantic_object,
    get_non_negative_int,
    get_optional_positive_int,
    get_optional_non_negative_int,
    validate_rna_type,
    get_unique_list_from_query_parameter,
)
from scimodom.services.bedtools import BedToolsService, get_bedtools_service
from scimodom.utils.dtos.bedtools import Bed6Record
from scimodom.services.file import get_file_service
from scimodom.utils.specs.enums import Strand, AssemblyFileType

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
class GeneSearch:
    gene_filter: list[str]
    chrom_filter: str | None = None
    chrom_start_filter: int | None = None
    chrom_end_filter: int | None = None


class IntersectResponse(BaseModel):
    records: list[Bed6Record]


@modification_api.route("/query", defaults={"by_gene": None}, methods=["GET"])
@modification_api.route("/query/<by_gene>")
@cross_origin(supports_credentials=True)
def get_modifications_as_json(by_gene):
    """Search view API."""
    try:
        data = _get_modifications_for_request(by_gene)
    except ClientResponseException as e:
        return e.response_tuple
    for r in data["records"]:
        r["strand"] = r["strand"].value
    return data


@modification_api.route("/csv", defaults={"by_gene": None}, methods=["GET"])
@modification_api.route("/csv/<by_gene>")
@cross_origin(supports_credentials=True)
def get_modifications_as_csv(by_gene):
    try:
        data = _get_modifications_for_request(by_gene)
    except ClientResponseException as e:
        return e.response_tuple
    records_as_csv = _get_csv_from_modifications_records(data["records"])
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
    """Get information related to a modification site."""
    try:
        taxa_id = get_valid_taxa_id()
        chrom, start, end, _ = get_valid_coords(taxa_id)
    except ClientResponseException as e:
        return e.response_tuple

    modification_service = get_modification_service()
    response = modification_service.get_modification_site(chrom, start, end)
    response["records"] = [
        {**r, "strand": r["strand"].value} for r in response["records"]
    ]
    return response


@modification_api.route("/genomic-context/<context>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genomic_sequence_context(context):
    """Get sequence context for a modification site."""
    try:
        taxa_id = get_valid_taxa_id()
        coords = get_valid_coords(taxa_id, context=int(context))
    except ClientResponseException as e:
        return e.response_tuple

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
    """Get information related to miRNA target and
    RBP binding sites that may be affected by a
    modification site."""
    try:
        with _ModificationContext(target_type) as ctx:
            records = ctx.bedtools_service.intersect_bed6_records(
                ctx.records, ctx.stream, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(IntersectResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


class _ModificationContext:
    @dataclass
    class Ctx:
        bedtools_service: BedToolsService
        records: Iterable[Bed6Record]
        is_strand: bool
        stream: TextIO

    def __init__(self, target_type: str):
        self._target_type = get_valid_targets_type(target_type)
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
    # TODO: chrom validation, cf. get_valid_coords
    if by_gene:
        gene_or_chrom = _get_gene_or_chrom_required()
        return modification_service.get_modifications_by_gene(
            annotation_source=_get_annotation_source(),
            taxa_id=get_valid_taxa_id(),
            gene_filter=gene_or_chrom.gene_filter,
            chrom=gene_or_chrom.chrom_filter,
            chrom_start=gene_or_chrom.chrom_start_filter,
            chrom_end=gene_or_chrom.chrom_end_filter,
            first_record=get_optional_non_negative_int("firstRecord"),
            max_records=get_optional_positive_int("maxRecords"),
            multi_sort=_get_multi_sort(),
        )
    else:
        return modification_service.get_modifications_by_source(
            annotation_source=_get_annotation_source(),
            modification_id=get_non_negative_int("modification"),
            organism_id=get_non_negative_int("organism"),
            technology_ids=_get_technology_ids(),
            taxa_id=get_valid_taxa_id(),
            gene_filter=_get_gene_filters(),
            chrom=request.args.get("chrom", type=str),
            chrom_start=get_optional_non_negative_int("chromStart"),
            chrom_end=get_optional_positive_int("chromEnd"),
            first_record=get_optional_non_negative_int("firstRecord"),
            max_records=get_optional_positive_int("maxRecords"),
            multi_sort=_get_multi_sort(),
        )


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


def _get_annotation_source():
    rna_type = request.args.get("rnaType", type=str)
    validate_rna_type(rna_type)
    return RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[rna_type]


# TODO: for mod, org, and tech, we should in fact check that they exists in the DB...
def _get_technology_ids():
    raw = get_unique_list_from_query_parameter("technology", int)
    if raw is None:
        return []
    for i in raw:
        if i < 0:
            raise ClientResponseException(400, "Invalid technology ID")
    return raw


def _get_gene_filters():
    raw = get_unique_list_from_query_parameter("geneFilter", str)
    if raw is None:
        return []
    return raw


def _get_gene_or_chrom_required() -> GeneSearch:
    gene = get_unique_list_from_query_parameter("geneFilter", str)
    if gene:
        return GeneSearch(gene_filter=gene)
    else:
        chrom = request.args.get("chrom", type=str)
        if not chrom:
            raise ClientResponseException(400, "Gene or chromosome is required")
        return GeneSearch(
            gene_filter=[],
            chrom_filter=chrom,
            chrom_start_filter=get_non_negative_int("chromStart"),
            chrom_end_filter=get_positive_int("chromEnd"),
        )


def _get_multi_sort(url_split: str = "%2B"):
    raw = get_unique_list_from_query_parameter("multiSort", str)
    if raw is None or (len(raw) == 1 and raw[0] == ""):
        return []
    for i in raw:
        field, direction = i.split(url_split)
        if field not in ["chrom", "score", "start", "coverage", "frequency"]:
            raise ClientResponseException(400, "Invalid table sort (multiSort) field")
        if direction not in ["desc", "asc"]:
            raise ClientResponseException(
                400, "Invalid table sort (multiSort) direction"
            )
    return raw
