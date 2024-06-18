from flask import Blueprint, request
from flask_cors import cross_origin

from scimodom.services.modification import get_modification_service

modification_api = Blueprint("modification_api", __name__)


@modification_api.route("/", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_search():
    """Search view API."""
    modification_id = request.args.get("modification", type=int)
    organism_id = request.args.get("organism", type=int)
    technology_ids = request.args.getlist("technology", type=int)
    taxa_id = request.args.get("taxid", type=int)
    gene_filter = request.args.getlist("geneFilter", type=str)
    chrom = request.args.get("chrom", type=str)
    chrom_start = request.args.get("chromStart", type=int)
    chrom_end = request.args.get("chromEnd", type=int)
    first_record = request.args.get("firstRecord", type=int)
    max_records = request.args.get("maxRecords", type=int)
    multi_sort = request.args.getlist("multiSort", type=str)

    print(f"************* {request.args}")

    modification_service = get_modification_service()
    response = modification_service.get_search(
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
    return response
