from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Iterable, Optional, TextIO

from flask import Blueprint, request
from flask_cors import cross_origin
from pydantic import BaseModel

from scimodom.services.annotation import RNA_TYPE_TO_ANNOTATION_SOURCE_MAP
from scimodom.services.modification import get_modification_service
from scimodom.api.helpers import (
    ClientResponseException,
    get_valid_coords,
    get_valid_targets_type,
    get_valid_taxa_id,
    get_response_from_pydantic_object,
)
from scimodom.services.bedtools import BedToolsService, get_bedtools_service
from scimodom.utils.bedtools_dto import Bed6Record
from scimodom.services.file import AssemblyFileType, get_file_service
from scimodom.utils.common_dto import Strand

logger = logging.getLogger(__name__)

modification_api = Blueprint("modification_api", __name__)


class IntersectResponse(BaseModel):
    records: list[Bed6Record]


@modification_api.route("/", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modifications():
    """Search view API."""
    modification_id = request.args.get("modification", type=int)
    organism_id = request.args.get("organism", type=int)
    technology_ids = request.args.getlist("technology", type=int)
    rna_type = request.args.get("rnaType", type=str)
    taxa_id = request.args.get("taxaId", type=int)
    gene_filter = request.args.getlist("geneFilter", type=str)
    chrom = request.args.get("chrom", type=str)
    chrom_start = request.args.get("chromStart", type=int)
    chrom_end = request.args.get("chromEnd", type=int)
    first_record = request.args.get("firstRecord", type=int)
    max_records = request.args.get("maxRecords", type=int)
    multi_sort = request.args.getlist("multiSort", type=str)

    annotation_source = RNA_TYPE_TO_ANNOTATION_SOURCE_MAP[rna_type]

    modification_service = get_modification_service()
    response = modification_service.get_modifications_by_source(
        annotation_source,
        modification_id,
        organism_id,
        technology_ids,
        taxa_id,
        gene_filter,
        chrom,
        chrom_start,
        chrom_end,
        first_record,
        max_records,
        multi_sort,
    )
    response["records"] = [
        {**r, "strand": r["strand"].value} for r in response["records"]
    ]
    return response


@modification_api.route("/sitewise", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification_sitewise():
    """Get information related to a modification site."""
    try:
        taxa_id = get_valid_taxa_id(request.args.get("taxaId"))
        chrom, start, end, _ = get_valid_coords(taxa_id)
        first_record = request.args.get("firstRecord", type=int)
        max_records = request.args.get("maxRecords", type=int)
        multi_sort = request.args.getlist("multiSort", type=str)
    except ClientResponseException as e:
        return e.response_tupel

    modification_service = get_modification_service()
    response = modification_service.get_modification_site(
        chrom, start, end, first_record, max_records, multi_sort
    )
    response["records"] = [
        {**r, "strand": r["strand"].value} for r in response["records"]
    ]
    return response


@modification_api.route("/genomic-context/<context>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genomic_sequence_context(context):
    """Get sequence context for a modification site."""
    try:
        taxa_id = get_valid_taxa_id(request.args.get("taxaId"))
        coords = get_valid_coords(taxa_id, context=int(context))
    except ClientResponseException as e:
        return e.response_tupel

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
        return e.response_tupel


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
        self._taxa_id = get_valid_taxa_id(request.args.get("taxaId"))
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
            name="",
            score=0,
            strand=coords[3],
        )
    ]
