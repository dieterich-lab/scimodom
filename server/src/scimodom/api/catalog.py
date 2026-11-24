from flask import Blueprint
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    get_optional_bool,
    get_optional_valid_taxa_id,
    get_required_list,
    get_valid_taxa_id,
    parse_valid_rna_type,
)
from scimodom.services.annotation import get_annotation_service
from scimodom.services.assembly import get_assembly_service
from scimodom.services.gene import get_gene_service
from scimodom.services.selection import get_selection_service
from scimodom.services.utilities import get_utilities_service

catalog_api = Blueprint("catalog_api", __name__)


@catalog_api.get("/rna-types")
def get_rna_types():
    """Get RNA types.

    :return: JSON array with RNA type information.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_utilities_service().get_rna_types()


@catalog_api.get("/rna-types/<rna_type>/biotypes")
def get_biotypes(rna_type: str):
    """Get biotypes.

    NOTE: <rna_type> unused

    :param rna_type: Incoming RNA type (unused)
    :return: JSON object with available biotypes
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_utilities_service().get_biotypes()


@catalog_api.get("/rna-types/<rna_type>/features")
def get_features(rna_type: str):
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
    try:
        rna_type = parse_valid_rna_type(rna_type)
        return {"features": get_annotation_service().get_features_by_rna_type(rna_type)}
    except ClientResponseException as exc:
        return exc.response_tuple
    except NotImplementedError:
        return create_error_response(
            501,
            f"rnaType '{rna_type}' not implemented",
        )


@catalog_api.get("/taxa")
def get_taxa():
    """Get species with taxonomic information.

    :return: JSON array with taxonomic information
    for each species.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_utilities_service().get_taxa()


@catalog_api.get("/chromosomes")
def get_chroms():
    """Get chromosomes and their size for a given taxon.

    Chromosomes only exist for the current assembly of
    a given taxon.

    :query taxaId: NCBI taxon (required)
    :return: JSON array with chromosomes and their size for the
    current assembly of the given taxon.
    :statuscode 200: OK
    :statuscode 400: Bad Request - missing or invalid Taxa ID
    :statuscode 404: Not Found - Taxa ID or chromosome-related data
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_valid_taxa_id()
        return get_assembly_service().get_chroms(taxa_id)
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


@catalog_api.get("/assemblies")
def get_assemblies():
    """Get installed assemblies.

    :query taxaId: Optional NCBI taxon to restrict the result to
    :query current: Optional, true for the current assemblies only,
    false for the others only. Omit for all of them
    :return: JSON array with assemblies.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid Taxa ID (cannot be
    coerced to int) or invalid value for current
    :statuscode 404: Not Found - Taxa ID
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_optional_valid_taxa_id()
        current = get_optional_bool("current")
        return get_assembly_service().get_assemblies(taxa_id, current)
    except ClientResponseException as exc:
        return exc.response_tuple


@catalog_api.get("/annotations")
def get_annotations():
    """Get current annotations.

    :query taxaId: Optional NCBI taxon to restrict the result to
    :return: JSON array with the current annotations.
    :statuscode 200: OK
    :statuscode 400: Bad Request - invalid Taxa ID (cannot be
    coerced to int)
    :statuscode 404: Not Found - Taxa ID
    :statuscode 500: Internal Server Error
    """
    try:
        taxa_id = get_optional_valid_taxa_id()
        return get_annotation_service().get_annotations(taxa_id)
    except ClientResponseException as exc:
        return exc.response_tuple


@catalog_api.get("/modomics")
def get_modomics():
    """Get modifications.

    :return: JSON array with MODOMICS nomenclature
    for all modifications.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_utilities_service().get_modomics()


@catalog_api.get("/methods")
def get_methods():
    """Get detection methods and their classification.

    :return: JSON array with classification information
    for all detection methods.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_utilities_service().get_methods()


@catalog_api.get("/selections")
def get_selections():
    """Get selections (modification, organism, technology).

    :return: JSON array with detailed information for
    all combinations of modifications, organisms, and
    technology that are available in the database.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    return get_selection_service().get_selections()


@catalog_api.get("/genes")
def get_genes():
    """Get genes for one or more selection(s).

    :query selection: One or more selection identifiers,
    associated with a combination of modification,
    organism, and technology (required)
    :return: Array with gene symbols
    :statuscode 200: OK
    :statuscode 400: Bad Request - missing selection
    :statuscode 404: Not Found - selection identifier
    :statuscode 500: Internal Server Error
    """
    try:
        selection_ids = get_required_list("selection", int)
        return get_gene_service().get_genes(selection_ids)
    except ClientResponseException as exc:
        return exc.response_tuple
    except NoResultFound:
        return create_error_response(
            404,
            f"No data for selection(s) '{', '.join([str(s) for s in selection_ids])}'",
        )
