from flask import Blueprint, request
from flask_cors import cross_origin
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    get_valid_taxa_id,
    ClientResponseException,
    validate_rna_type,
)
from scimodom.services.annotation import get_annotation_service
from scimodom.services.assembly import get_assembly_service
from scimodom.services.file import get_file_service
from scimodom.services.utilities import get_utilities_service
from scimodom.utils.specifications import BIOTYPES

api = Blueprint("api", __name__)


MAPPED_BIOTYPES = sorted(list(set(BIOTYPES.values())))


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
    file_service = get_file_service()
    selection_ids = request.args.getlist("selection[]", type=int)
    try:
        return file_service.get_gene_cache(selection_ids)
    except FileNotFoundError:
        return {"message": "No data found for these selection."}, 404


@api.route("/biotypes/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_biotypes(rna_type):
    # TODO: do biotypes also depend on RNA type/annotation?
    return {"biotypes": MAPPED_BIOTYPES}


@api.route("/features/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_features(rna_type):
    annotation_service = get_annotation_service()
    try:
        validate_rna_type(rna_type)
        return {"features": annotation_service.get_features_by_rna_type(rna_type)}
    except ClientResponseException as e:
        return e.response_tupel
    except NotImplementedError:
        return {"message": f"RNA type '{rna_type}' not implemented."}, 501


@api.route("/chroms/<taxa_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chroms(taxa_id: str):
    assembly_service = get_assembly_service()
    try:
        taxa_id_as_int = get_valid_taxa_id(taxa_id)
        return assembly_service.get_chroms(taxa_id_as_int)
    except ClientResponseException as e:
        return e.response_tupel
    except NoResultFound:
        return {"message": "No chrom data available for this taxa (1)."}, 404
    except FileNotFoundError:
        return {"message": "No chrom data available for this taxa (2)."}, 404


@api.route("/assembly/<taxid>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assemblies(taxid):
    utilities_service = get_utilities_service()
    return utilities_service.get_assemblies(taxid)
