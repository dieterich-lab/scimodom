"""Provide semantically valid data.

- Domain and business constraints validation
- Validation helpers (input and domain validation)
- Permission validation
"""

from flask import request
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.database.models import BamFile, Dataset, User
from scimodom.services.annotation import get_annotation_service
from scimodom.services.assembly import get_assembly_service
from scimodom.services.dataset import DatasetService, get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import NoSuchUser, get_user_service
from scimodom.services.utilities import get_utilities_service
from scimodom.utils.specs.enums import (
    Identifiers,
    Strand,
)

from .errors import _invalid_choice, ClientResponseException
from .input import (
    _positive_int,
    _parse_param,
    _get_required_query_param,
    _get_optional_query_param,
    _is_valid_identifier,
    _validate_file_name,
    get_positive_int,
    get_non_negative_int,
    get_required_list,
    get_optional_list,
    validate_file_name,
)


# Domain and business constraints validation


def validate_chrom(
    taxa_id: int, chrom: str, start: int | None, end: int | None
) -> None:
    """Validate chromosome, start and/or end.

    NOTE: Presence or absence of start/end, where
    relevant, must be validated by the caller.

    :param taxa_id: A fully validated taxon identifier
    :param chrom: A syntactically valid chromosome
    :param start: A syntactically valid chromosome
    start or None
    :param end: A syntactically valid chromosome
    end or None
    :raises ClientResponseException: 400, 404
    """
    _validate_chrom(taxa_id, chrom, start, end)


# Validation helpers (input and domain validation)


def get_valid_rna_type() -> str:
    """Parse query for RNA type and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated RNA type
    """
    rna_type = _get_required_query_param("rnaType")
    _validate_rna_type(rna_type)
    return rna_type


def parse_valid_rna_type(raw: str) -> str:
    """Parse raw RNA type and validate.

    :param raw: Route parameter for RNA type
    :raises ClientResponseException: 400, 404
    :return: The validated RNA type
    """
    rna_type = _parse_param("rnaType", raw)
    _validate_rna_type(rna_type)
    return rna_type


def get_valid_taxa_id() -> int:
    """Parse query for taxon identifier and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated taxon identifier
    """
    taxa_id = get_positive_int("taxaId")
    _validate_taxa_id(taxa_id)
    return taxa_id


def parse_valid_taxa_id(raw: str) -> int:
    """Parse raw taxon identifier and validate.

    :param raw: Route parameter for taxon identifier
    :raises ClientResponseException: 400, 404
    :return: The validated taxon identifier
    """
    taxa_id = _parse_param("taxa_id", raw, _positive_int)
    _validate_taxa_id(taxa_id)
    return taxa_id


def get_optional_valid_biotypes() -> list[str]:
    """Parse query for biotypes and validate.

    NOTE: May return an empty list.

    :raises ClientResponseException: 400, 404
    :return: The validated list of biotypes
    """
    rna_type = get_valid_rna_type()
    biotypes = get_optional_list("biotypes", str)
    _validate_biotypes(biotypes, rna_type)
    return biotypes


def get_optional_valid_features() -> list[str]:
    """Parse query for features and validate.

    NOTE: May return an empty list.

    :raises ClientResponseException: 400, 404, 501
    :return: The validated list of features
    """
    rna_type = get_valid_rna_type()
    features = get_optional_list("features", str)
    _validate_features(features, rna_type)
    return features


def get_valid_selections() -> tuple[int, int, list[int]]:
    """Parse query for selections and validate.

    :raises ClientResponseException: 400, 404
    :return: The validated modification, organism, and
    technology identifiers
    """
    modification_id = get_non_negative_int("modification")
    organism_id = get_non_negative_int("organism")
    technology_ids = get_required_list("technology", int)
    selections = [(modification_id, organism_id, tid) for tid in technology_ids]
    _validate_selections(selections)
    return modification_id, organism_id, technology_ids


def get_valid_coords(
    context: int = 0,
) -> tuple[str, int, int, Strand]:
    """Parse query for coordinates and validate.

    NOTE: This function uses "start" and "end",
    not "chromStart", "chromEnd".

    :param context: Number of bases to include in
    context around start-end.
    :raises ClientResponseException: 400, 404
    :return: Coordinates as (chrom, start, end, strand)
    where strand defaults to Strand.UNDEFINED (".")
    """
    taxa_id = get_valid_taxa_id()
    chrom = _get_required_query_param("chrom")
    start = get_non_negative_int("start")
    end = get_positive_int("end")
    chrom_sizes = _get_chroms(taxa_id)
    _validate_chrom(taxa_id, chrom, start, end, chrom_sizes)

    strand = request.args.get("strand", default=".", type=str)
    try:
        strand_dto = Strand(strand)
    except ValueError:
        _invalid_choice("strand", strand, "+, -, or .")

    if context > 0:
        start = start - context
        start = max(start, 0)
        end = end + context
        end = min(end, chrom_sizes[chrom])

    return chrom, start, end, strand_dto


def parse_valid_dataset(raw: str) -> Dataset:
    """Parse a valid dataset and return the matching object.

    :param raw: Route parameter for dataset identifier
    :raises ClientResponseException: 400, 404.
    :return: Dataset
    """
    dataset_id = _parse_param("datasetId", raw)
    dataset_service = get_dataset_service()
    return _get_valid_dataset_by_id(dataset_id, dataset_service)


def parse_valid_bam(dataset: Dataset, raw: str) -> BamFile:
    """Parse a valid BAM file and return the matching object.

    :param dataset: Dataset
    :param raw: Route parameter file name
    :raises ClientResponseException: 400, 404.
    :return: BAM file object
    """
    validate_file_name("BAM", raw)
    file_service = get_file_service()
    try:
        return file_service.get_bam_file(dataset, raw)
    except NoResultFound:
        raise ClientResponseException(
            404,
            f"BAM file '{raw}' not found or "
            f"no association with dataset '{dataset.id}'",
        )


def get_optional_valid_dataset_id_list(
    name: str,
    max_ids_in_list: int,
) -> list[str]:
    """Get a list of valid dataset IDs.

    NOTE: May return an empty list.

    :param name: Query parameter name
    :param max_ids_in_list: Maximum list length
    :raises ClientResponseException: 400, 404.
    :return: List of valid dataset identifier(s)
    or an empty list
    """
    id_list = get_optional_list(name, str)
    if len(id_list) > max_ids_in_list:
        raise ClientResponseException(
            400,
            f"'{name}' contains too many datasetId " f"(max. {max_ids_in_list})",
        )
    dataset_service = get_dataset_service()
    return [_get_valid_dataset_by_id(d, dataset_service).id for d in id_list]


def get_optional_valid_tmp_file_id(name: str) -> str | None:
    """Get uploaded/temporary file identifier.

    :param name: Query parameter name
    :param is_optional: True if parameter is required (Default: False)
    :raises ClientResponseException: 400, 404
    :return: Uploaded/temporary file identifier or None
    """
    file_id = _get_optional_query_param(name)
    if file_id is not None:
        _validate_file_name(name, file_id)
        file_service = get_file_service()
        if not file_service.check_tmp_upload_file_id(file_id):
            raise ClientResponseException(
                404,
                f"{name} file not found",
                "Select the file again and try to re-upload",
            )
    return file_id


# Permission validation


def validate_project_write_permission(smid: str) -> None:
    """Validate if user is allowed to add datasets to the given project.

    :param smid: Project identifier (SMID)
    :raises ClientResponseException: 403, 404
    """
    permission_service = get_permission_service()
    user = _get_valid_user()
    if not permission_service.may_change_project(user, smid):
        raise ClientResponseException(
            403,
            f"Forbidden to access project '{smid}'",
        )


def validate_dataset_write_permission(dataset: Dataset) -> None:
    """Validate if a user is allowed to modify a dataset.

    :param smid: Dataset
    :raises ClientResponseException: 403, 404
    """
    permission_service = get_permission_service()
    user = _get_valid_user()
    if not permission_service.may_change_dataset(user, dataset):
        raise ClientResponseException(
            403,
            f"Forbidden to access dataset '{dataset.id}'",
        )


# Private


def _get_chroms(taxa_id: int) -> dict[str, int]:
    assembly_service = get_assembly_service()
    chrom_sizes: dict[str, int] = {
        d["chrom"]: d["size"] for d in assembly_service.get_chroms(taxa_id)
    }
    return chrom_sizes


def _validate_chrom(
    taxa_id: int,
    chrom: str,
    start: int | None,
    end: int | None,
    chrom_sizes: dict[str, int] | None = None,
) -> None:
    if chrom_sizes is None:
        chrom_sizes = _get_chroms(taxa_id)
    if chrom not in chrom_sizes:
        raise ClientResponseException(
            404, f"chrom '{chrom}' for taxaId '{taxa_id}' not found"
        )

    this_chrom_size = chrom_sizes[chrom]
    start = start if start is not None else 0
    end = end if end is not None else this_chrom_size
    if end <= start:
        raise ClientResponseException(
            400,
            "Parameter 'end'/'chromEnd' must be greater than "
            f"'start'/'chromStart' (start is: {start}, got end: {end})",
        )
    if not end <= this_chrom_size:
        raise ClientResponseException(
            400,
            "Parameter 'end'/'chromEnd' is greater than chrom size "
            f"(max. allowed: {this_chrom_size}, got '{end}')",
        )


def _validate_rna_type(rna_type: str) -> None:
    utilities_service = get_utilities_service()
    valid_rna_types = [obj["id"] for obj in utilities_service.get_rna_types()]
    if rna_type not in valid_rna_types:
        raise ClientResponseException(
            404,
            f"rnaType '{rna_type}' not found",
            "Use GET /catalogs/rna-types for valid RNA types",
        )


def _validate_taxa_id(taxa_id: int) -> None:
    utilities_service = get_utilities_service()
    valid_taxa_ids = [obj["taxa_id"] for obj in utilities_service.get_taxa()]
    if taxa_id not in valid_taxa_ids:
        raise ClientResponseException(
            404,
            f"taxaId '{taxa_id}' not found",
            "Use GET /catalogs/taxa for valid taxa",
        )


# TODO MS14
# biotypes are independent of species/RNA type
def _validate_biotypes(biotypes: list[str], rna_type: str) -> None:
    utilities_service = get_utilities_service()
    valid_biotypes = utilities_service.get_biotypes()["biotypes"]
    unknown_biotypes = [
        biotype for biotype in biotypes if biotype not in valid_biotypes
    ]
    if unknown_biotypes:
        raise ClientResponseException(
            404,
            f"biotypes '{', '.join(unknown_biotypes)}' not found",
            "Use GET /catalogs/rna-types/<rnaType>/biotypes for valid biotypes",
        )


# TODO MS14
def _validate_features(features: list[str], rna_type: str) -> None:
    annotation_service = get_annotation_service()
    try:
        valid_features = annotation_service.get_features_by_rna_type(rna_type)
    except NotImplementedError as exc:
        raise ClientResponseException(
            501, f"rnaType '{rna_type}' not implemented"
        ) from exc
    unknown_features = [
        feature for feature in features if feature not in valid_features
    ]
    if unknown_features:
        raise ClientResponseException(
            404,
            f"features '{', '.join(unknown_features)}' not found",
            "Use GET /catalogs/rna-types/<rnaType>/features for valid features",
        )


def _validate_selections(selections: list[tuple[int, int, int]]) -> None:
    utilities_service = get_utilities_service()
    valid_selections = [
        (obj["modification_id"], obj["organism_id"], obj["technology_id"])
        for obj in utilities_service.get_selections()
    ]
    unknown_selections = [s for s in selections if s not in valid_selections]
    if unknown_selections:
        raise ClientResponseException(
            404,
            (
                "(modification, organism, technology) "
                f"'{', '.join(map(str, unknown_selections))}' not found."
            ),
            (
                "Use GET /catalogs/selections for valid combinations of "
                "modification, organism, and technology identifiers"
            ),
        )


def _get_valid_user() -> User:
    email = get_jwt_identity()
    user_service = get_user_service()
    try:
        return user_service.get_user_by_email(email)
    except NoSuchUser:
        raise ClientResponseException(404, f"User '{email}' not found")


def _get_valid_dataset_by_id(dataset_id: str, dataset_service: DatasetService):
    if not _is_valid_identifier(dataset_id, Identifiers.EUFID.length):
        raise ClientResponseException(400, f"Invalid datasetId '{dataset_id}'")
    try:
        return dataset_service.get_by_id(dataset_id)
    except NoResultFound as exc:
        raise ClientResponseException(
            404, f"datasetId '{dataset_id}' not found"
        ) from exc
