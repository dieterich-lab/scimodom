from flask import Blueprint, Response
from flask_cors import cross_origin
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    get_valid_logo,
    get_valid_taxa_id_from_string,
    ClientResponseException,
    validate_rna_type,
    get_unique_list_from_query_parameter,
    create_error_response,
)
from scimodom.services.annotation import get_annotation_service, BIOTYPES
from scimodom.services.assembly import get_assembly_service
from scimodom.services.gene import get_gene_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.services.utilities import get_utilities_service
from scimodom.utils.specs.enums import SunburstChartType

api = Blueprint("api", __name__)


BUFFER_SIZE = 1024 * 1024
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
    gene_service = get_gene_service()
    selection_ids = get_unique_list_from_query_parameter("selection", int)
    try:
        return gene_service.get_genes(selection_ids)
    except FileNotFoundError:
        return create_error_response(404, "No data found for these selection")


@api.route("/biotypes/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_biotypes(rna_type):  # noqa
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
        return e.response_tuple
    except NotImplementedError:
        return create_error_response(501, f"RNA type '{rna_type}' not implemented.")


@api.route("/chroms/<taxa_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chroms(taxa_id: str):
    assembly_service = get_assembly_service()
    try:
        taxa_id_as_int = get_valid_taxa_id_from_string(taxa_id)
        return assembly_service.get_chroms(taxa_id_as_int)
    except ClientResponseException as e:
        return e.response_tuple
    except NoResultFound:
        return create_error_response(404, "No chrom data available for this taxa (1).")
    except FileNotFoundError:
        return create_error_response(404, "No chrom data available for this taxa (2).")


@api.route("/assembly/<taxa_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assemblies(taxa_id):
    utilities_service = get_utilities_service()
    try:
        taxa_id_as_int = get_valid_taxa_id_from_string(taxa_id)
        return utilities_service.get_assemblies(taxa_id_as_int)
    except ClientResponseException as e:
        return e.response_tuple


@api.route("/logos/<motif>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_logo_file(motif):
    try:
        return {"image": get_valid_logo(motif).as_posix()}
    except ClientResponseException as e:
        return e.response_tuple


@api.route("/sunburst/<chart>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_sunburst_chart(chart):
    try:
        cooked_type = SunburstChartType(chart)
    except ValueError:
        return create_error_response(404, "Unrecognized chart type.")
    sunburst_service = get_sunburst_service()

    def generate():
        with sunburst_service.open_json(cooked_type) as fp:
            while True:
                buffer = fp.read(BUFFER_SIZE)
                if len(buffer) == 0:
                    break
                yield buffer

    return Response(
        generate(),
        mimetype="application/json",
    )


@api.route("/release", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_release():
    utitlies_service = get_utilities_service()
    return utitlies_service.get_release_info()
