import os
from pathlib import Path

from flask import Blueprint, request
from flask_cors import cross_origin

from scimodom.services.public import get_public_service

api = Blueprint("api", __name__)


@api.route("/genes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genes():
    selection_ids = request.args.getlist("selection", type=int)
    public_service = get_public_service()
    return public_service.get_gene_list(selection_ids)


@api.route("/features_biotypes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_feature_biotypes():
    public_service = get_public_service()
    return public_service.get_features_and_biotypes()


@api.route("/rna_types", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_rna_types():
    public_service = get_public_service()
    return public_service.get_rna_types()


@api.route("/modification", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification():
    public_service = get_public_service()
    return public_service.get_modomics()


@api.route("/method", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_method():
    public_service = get_public_service()
    return public_service.get_detection_method()


@api.route("/taxid", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxid():
    public_service = get_public_service()
    return public_service.get_taxa()


@api.route("/assembly/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assembly(taxid):
    public_service = get_public_service()
    return public_service.get_assembly_for_taxid(taxid)


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    public_service = get_public_service()
    return public_service.get_selection()


@api.route("/chrom/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chrom(taxid):
    public_service = get_public_service()
    return public_service.get_chrom(taxid)


@api.route("/search", methods=["GET"])
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

    public_service = get_public_service()
    response = public_service.get_search(
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
