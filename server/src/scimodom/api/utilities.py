import os
from pathlib import Path

from flask import Blueprint, request
from flask_cors import cross_origin

from scimodom.services.utilities import get_utilities_service

api = Blueprint("api", __name__)


@api.route("/genes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genes():
    selection_ids = request.args.getlist("selection", type=int)
    public_service = get_utilities_service()
    return public_service.get_gene_list(selection_ids)


@api.route("/features_biotypes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_feature_biotypes():
    public_service = get_utilities_service()
    return public_service.get_features_and_biotypes()


@api.route("/rna_types", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_rna_types():
    public_service = get_utilities_service()
    return public_service.get_rna_types()


@api.route("/modification", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modification():
    public_service = get_utilities_service()
    return public_service.get_modomics()


@api.route("/method", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_method():
    public_service = get_utilities_service()
    return public_service.get_detection_method()


@api.route("/taxid", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxid():
    public_service = get_utilities_service()
    return public_service.get_taxa()


@api.route("/assembly/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assembly(taxid):
    public_service = get_utilities_service()
    return public_service.get_assembly_for_taxid(taxid)


@api.route("/selection", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selection():
    public_service = get_utilities_service()
    return public_service.get_selection()


@api.route("/chrom/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chrom(taxid):
    public_service = get_utilities_service()
    return public_service.get_chrom(taxid)
