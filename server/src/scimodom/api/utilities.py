from flask import Blueprint, Response
from flask_cors import cross_origin
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    parse_valid_taxa_id,
    parse_valid_rna_type,
    get_unique_list_from_query_param,
    parse_valid_chart_type,
)
from scimodom.services.annotation import get_annotation_service
from scimodom.services.assembly import get_assembly_service
from scimodom.services.gene import get_gene_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.services.utilities import get_utilities_service

api = Blueprint("api", __name__)


BUFFER_SIZE = 1024 * 1024


@api.route("/rna-types", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_rna_types():
    """Get RNA types.

    :return: JSON array with RNA type information.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_rna_types()


@api.route("/taxa", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_taxa():
    """Get species with taxonomic information.

    :return: JSON array with taxonomic information
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

    :return: JSON array with MODOMICS nomenclature
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

    :return: JSON array with classification information
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

    :return: JSON array with detailed information for
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
    :return: Array with gene symbols
    :statuscode 200: OK
    :statuscode 404: Not Found - selection identifier
    :statuscode 500: Internal Server Error
    """
    gene_service = get_gene_service()
    selection_ids = get_unique_list_from_query_param("selection", int)
    try:
        return gene_service.get_genes(selection_ids)
    except NoResultFound:
        return create_error_response(
            404,
            f"No data for selection(s) '{', '.join([str(s) for s in selection_ids])}'",
        )


@api.route("/biotypes/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_biotypes(rna_type):  # noqa
    """Get biotypes.

    NOTE: <rna_type> unused

    :param rna_type: Incoming RNA type (unused)
    :return: JSON object with available biotypes
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    utilities_service = get_utilities_service()
    return utilities_service.get_biotypes()


@api.route("/features/<rna_type>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_features(rna_type):
    """Get features.

    :param rna_type: Incoming RNA type
    :return: JSON object with available features for
    a given rna_type
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid RNA type (empty)
    :statuscode 404: Not found - RNA type
    :statuscode 500: Internal Server Error
    :statuscode 501: Not Implemented - RNA type annotation
    """
    annotation_service = get_annotation_service()
    try:
        rna_type = parse_valid_rna_type(rna_type)
        return {"features": annotation_service.get_features_by_rna_type(rna_type)}
    except ClientResponseException as exc:
        return exc.response_tuple
    except NotImplementedError:
        return create_error_response(
            501,
            f"rnaType '{rna_type}' not implemented",
        )


@api.route("/chroms/<taxa_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_chroms(taxa_id: str):
    """Get chromosomes and their size for a given taxon.

    :param taxa_id: NCBI taxon (identifier)
    :return: JSON array with chromosome and their size for
    the current assembly for the given taxon.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid Taxa ID (cannot be coerced to int)
    :statuscode 404: Not Found - Taxa ID or chromosome-related data
    :statuscode 422: Unprocessable Content - Taxa ID not a positive int
    :statuscode 500: Internal Server Error
    """
    assembly_service = get_assembly_service()
    try:
        taxa_id_as_int = parse_valid_taxa_id(taxa_id)
        return assembly_service.get_chroms(taxa_id_as_int)
    except ClientResponseException as exc:
        return exc.response_tuple
    except NoResultFound:
        return create_error_response(
            404,
            f"No chrom data for taxaId '{taxa_id}' (1)",
        )
    except FileNotFoundError:
        return create_error_response(
            404,
            f"No chrom data for taxaId '{taxa_id}' (2)",
        )


@api.route("/assemblies/<taxa_id>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_assemblies(taxa_id):
    """Get assemblies for a given taxon.

    :param taxa_id: NCBI taxon (identifier)
    :return: JSON array with all available assemblies
    for the given taxon.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid Taxa ID (cannot be coerced to int)
    :statuscode 404: Not Found - Taxa ID
    :statuscode 422: Unprocessable Content - Taxa ID not a positive int
    :statuscode 500: Internal Server Error
    """
    assembly_service = get_assembly_service()
    try:
        taxa_id_as_int = parse_valid_taxa_id(taxa_id)
        assemblies = assembly_service.get_assemblies_by_taxa(taxa_id_as_int)
        return [{"id": assembly.id, "name": assembly.name} for assembly in assemblies]
    except ClientResponseException as exc:
        return exc.response_tuple


@api.route("/sunburst/<chart>", methods=["GET"])
@cross_origin(supports_credentials=True)
def get_sunburst_chart(chart):
    """Get sunburst chart data.

    :param chart: chart type
    :return: JSON object to generate one of the
    sunburst charts.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid chart (empty)
    :statuscode 422: Unprocessable Content - invalid chart type
    :statuscode 500: Internal Server Error
    """
    try:
        chart = parse_valid_chart_type(chart)
        sunburst_service = get_sunburst_service()
    except ClientResponseException as exc:
        return exc.response_tuple

    def generate():
        with sunburst_service.open_json(chart) as fp:
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
