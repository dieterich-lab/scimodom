import os
from pathlib import Path

from flask import Blueprint, request
from flask_cors import cross_origin

from scimodom.services.utilities import get_utilities_service

api = Blueprint("api", __name__)


@api.route("/rna_types", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_rna_types():
    utilities_service = get_utilities_service()
    return utilities_service.get_rna_types()


@api.route("/taxa", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxa():
    utilities_service = get_utilities_service()
    return utilities_service.get_taxa()


@api.route("/modomics", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modomics():
    utilities_service = get_utilities_service()
    return utilities_service.get_modomics()


@api.route("/methods", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_methods():
    utilities_service = get_utilities_service()
    return utilities_service.get_methods()


@api.route("/selections", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selections():
    utilities_service = get_utilities_service()
    return utilities_service.get_selections()


@api.route("/genes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genes():
    selection_ids = request.args.getlist("selection", type=int)
    # TODO validate selection ids
    utilities_service = get_utilities_service()
    return utilities_service.get_genes(selection_ids)


@api.route("/annotation/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_annotation(rna_type):
    utilities_service = get_utilities_service()
    # TODO process rna type into annotation  source
    annotation_source = "XXX"
    return utilities_service.get_annotation(annotation_source)


# TODO validate taxid
@api.route("/chroms/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chroms(taxid):
    utilities_service = get_utilities_service()
    return utilities_service.get_chroms(taxid)


@api.route("/assembly/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assemblies(taxid):
    utilities_service = get_utilities_service()
    return utilities_service.get_assemblies(taxid)
