from flask import Blueprint, Response
from flask_cors import cross_origin
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
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
    """Get RNA types.

    :returns: JSON array with RNA type information.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_rna_types()


@api.route("/taxa", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxa():
    """Get species with taxonomic information.

    :returns: JSON array with taxonomic information
    for each species.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_taxa()


@api.route("/modomics", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_modomics():
    """Get modifications.

    :returns: JSON array with MODOMICS nomenclature
    for all modifications.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_modomics()


@api.route("/methods", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_methods():
    """Get detection methods and their classification.

    :returns: JSON array with classification information
    for all detection methods.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_methods()


@api.route("/selections", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_selections():
    """Get selections (modification, organism, technology).

    :returns: JSON array with detailed information for
    all combinations of modifications, organisms, and
    technology that are available in the database.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_selections()


@api.route("/genes", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_genes():
    """Get genes for one or more selection(s).

    :query selection: A selection identifier
    (associated with a combination of modification,
    organism, and technology)
    :returns: Array with gene symbols
    :statuscode 200: OK
    :statuscode 404: Unrecognized selection identifier (not found)
    :statuscode 500: Internal Server Error
    """
    gene_service = get_gene_service()
    selection_ids = get_unique_list_from_query_parameter("selection", int)
    try:
        return gene_service.get_genes(selection_ids)
    except NoResultFound:
        return create_error_response(404, "No data for queried selection(s)")


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
    """Get chromosomes and their size for a given taxon.

    :param taxa_id: NCBI taxon (identifier)
    :returns: JSON array with chromosome and their size for
    the current assembly for the given taxon.
    :statuscode 200: OK
    :statuscode 400: Invalid Taxa ID (cannot be coerced to int)
    :statuscode 404: Unrecognized Taxa ID (unknown or unavailable taxon)
    :statuscode 500: Internal Server Error
    """
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
    """Get assemblies for a given taxon.

    :param taxa_id: NCBI taxon (identifier)
    :returns: JSON array with all available assemblies
    for the given taxon.
    :statuscode 200: OK
    :statuscode 400: Invalid Taxa ID (cannot be coerced to int)
    :statuscode 404: Unrecognized Taxa ID (unknown or unavailable taxon)
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    try:
        taxa_id_as_int = get_valid_taxa_id_from_string(taxa_id)
        return utilities_service.get_assemblies(taxa_id_as_int)
    except ClientResponseException as e:
        return e.response_tuple


@api.route("/sunburst/<chart>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_sunburst_chart(chart):
    """Get sunburst chart data.

    :param chart: chart type
    :returns: JSON object to generate one of the
    sunburst charts.
    :statuscode 200: OK
    :statuscode 404: Unrecognized chart type
    :statuscode 500: Internal Server Error
    """
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
    """Get number of sites and datasets for current release.

    :returns: JSON object with number of sites
    and datasets.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utitlies_service = get_utilities_service()
    return utitlies_service.get_release_info()
