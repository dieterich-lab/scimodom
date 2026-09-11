import logging
from dataclasses import dataclass
from typing import Generator, Iterable, Sequence, TextIO

from flask import Blueprint
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel

from scimodom.api.helpers import (
    ClientResponseException,
    get_valid_dataset_id_list_from_request_parameter,
    get_valid_tmp_file_id_from_request_parameter,
    get_valid_remote_file_name_from_request_parameter,
    get_valid_boolean_from_request_parameter,
    get_valid_taxa_id,
    get_response_from_pydantic_object,
)
from scimodom.services.assembly import LiftOverError
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.data import get_data_service
from scimodom.services.user import get_user_service
from scimodom.services.validator import (
    get_validator_service,
    SpecsError,
    DatasetHeaderError,
    DatasetImportError,
)
from scimodom.utils.importer.bed_importer import (
    Bed6Importer,
    EufImporter,
    BedImportTooManyErrors,
    BedImportEmptyFile,
)
from scimodom.utils.dtos.bedtools import (
    EufRecord,
    Bed6Record,
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
    ComparisonRecord,
)
from scimodom.utils.specs.enums import Identifiers

logger = logging.getLogger(__name__)

dataset_api = Blueprint("dataset_api", __name__)


class IntersectResponse(BaseModel):
    """DTO for intersect records."""

    records: list[IntersectRecord]


class ClosestResponse(BaseModel):
    """DTO for closest records."""

    records: list[ClosestRecord]


class SubtractResponse(BaseModel):
    """DTO for subtract records."""

    records: list[SubtractRecord]


@dataset_api.route("/list_all", methods=["GET"])
def list_all():
    """Get all dataset.

    :returns: JSON array with all available dataset
    and related metadata.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    dataset_service = get_dataset_service()
    return dataset_service.get_datasets()


@dataset_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    """Get dataset associated with user.

    This endpoint is restricted to authenticated users.
    A call to "get_user_by_email" may raise a "NoSuchUser"
    exception, but this should not happen in practice.
    If it does, it will be caught by the 500.

    :param header: The request header with current token.
    :returns: JSON array with all available dataset
    and related metadata.
    :statuscode 200: OK
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    dataset_service = get_dataset_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return dataset_service.get_datasets(user)


@dataset_api.route("/intersect", methods=["GET"])
@cross_origin(supports_credentials=True)
def intersect():
    """Intersect two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :returns: JSON object with JSON array of
    intersected records.
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed or missing parameters,
    invalid identifiers, too many dataset)
    :statuscode 404: Dataset, file, or taxon not found
    :statuscode 422: Unprocessable Content (empty file or
    too many skipped records)
    :statuscode 500: Internal Server Error (e.g. failed liftover)
    """
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.intersect_comparison_records(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(IntersectResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


@dataset_api.route("/closest", methods=["GET"])
@cross_origin(supports_credentials=True)
def closest():
    """Intersect (non-overlap) two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :returns: JSON object with JSON array of
    intersected (non-overlap) records.
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed or missing parameters,
    invalid identifiers, too many dataset)
    :statuscode 404: Dataset, file, or taxon not found
    :statuscode 422: Unprocessable Content (empty file or
    too many skipped records)
    :statuscode 500: Internal Server Error (e.g. failed liftover)
    """
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.closest_comparison_records(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(ClosestResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


@dataset_api.route("/subtract", methods=["GET"])
@cross_origin(supports_credentials=True)
def subtract():
    """Subtract two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :returns: JSON object with JSON array of
    subtracted records.
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed or missing parameters,
    invalid identifiers, too many dataset)
    :statuscode 404: Dataset, file, or taxon not found
    :statuscode 422: Unprocessable Content (empty file or
    too many skipped records)
    :statuscode 500: Internal Server Error (e.g. failed liftover)
    """
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.subtract_comparison_records(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(SubtractResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


class _CompareContext:
    @dataclass
    class Ctx:
        bedtools_service: BedToolsService
        a_records: Iterable[ComparisonRecord]
        b_records_list: Sequence[Iterable[ComparisonRecord]]
        is_strand: bool

    def __init__(self):
        self._reference_ids = get_valid_dataset_id_list_from_request_parameter(
            "reference"
        )
        self._comparison_ids = get_valid_dataset_id_list_from_request_parameter(
            "comparison"
        )
        self._upload_id = get_valid_tmp_file_id_from_request_parameter(
            "upload", is_optional=True
        )
        self._upload_name = get_valid_remote_file_name_from_request_parameter(
            "upload_name"
        )
        self._is_strand = get_valid_boolean_from_request_parameter(
            "strand", default=True
        )
        self._is_euf = get_valid_boolean_from_request_parameter("euf", default=False)
        self._taxa_id: int | None = None
        if self._is_euf:
            try:
                self._taxa_id = get_valid_taxa_id()
            except ClientResponseException as exc:
                response, status_code = exc.response_tuple
                message = response["message"]
                raise ClientResponseException(
                    status_code,
                    message,
                    f"Request needs a valid 'taxaId' when 'euf=true': {message}",
                ) from exc
        self._tmp_file_handle: TextIO | None = None

        if self._upload_id is None and len(self._comparison_ids) == 0:
            raise ClientResponseException(
                400, "Request is missing 'upload' or 'comparison'"
            )
        if self._upload_id is not None and len(self._comparison_ids) > 0:
            raise ClientResponseException(
                400, "Request can only handle 'upload' or 'comparison', but not both"
            )
        self._data_service = get_data_service()
        self._validator_service = get_validator_service()

    def __enter__(self) -> Ctx:
        if self._upload_id is None:
            # The MySQL driver does not allow to have multiple queries run at once;
            # we have to buffer the b_records in memory
            b_records_list = [
                list(self._get_comparison_records_from_db([dataset_id]))
                for dataset_id in self._comparison_ids
            ]
        else:
            file_service = get_file_service()
            try:
                self._tmp_file_handle = file_service.open_tmp_upload_file_by_id(
                    self._upload_id
                )
            except FileNotFoundError as exc:
                raise ClientResponseException(
                    404,
                    "Upload file ID not found"
                    "File not found - Select the file again and try to re-upload",
                ) from exc
            b_records_list = [list(self._get_comparison_records_from_file())]

        a_records = self._get_comparison_records_from_db(self._reference_ids)
        return self.Ctx(
            bedtools_service=get_bedtools_service(),
            a_records=a_records,
            b_records_list=b_records_list,
            is_strand=self._is_strand,
        )

    def _get_comparison_records_from_db(
        self, dataset_ids
    ) -> Generator[ComparisonRecord, None, None]:
        for dataset_id in dataset_ids:
            for data in self._data_service.get_by_dataset(dataset_id):
                yield ComparisonRecord(
                    chrom=data.chrom,
                    start=data.start,
                    end=data.end,
                    name=data.name,
                    score=data.score,
                    strand=data.strand,
                    eufid=data.dataset_id,
                    coverage=data.coverage,
                    frequency=data.frequency,
                )

    def _get_comparison_records_from_file(
        self,
    ) -> Generator[ComparisonRecord, None, None]:
        generator, context = self._import_with_context()
        try:
            for record in generator:
                raw_record = record.model_dump()
                yield ComparisonRecord(**raw_record, **context)
        except BedImportEmptyFile as exc:
            raise ClientResponseException(
                422, str(exc), "File upload failed. The file is empty."
            ) from exc
        except BedImportTooManyErrors as exc:
            raise ClientResponseException(
                422,
                str(exc),
                f"File upload failed. Too many skipped records:\n{exc.error_summary}\n"
                "Modify the file to conform to the latest bedRMod format specifications or\n"
                "try toggling the BED6 option to ignore validation.",
            ) from exc
        except LiftOverError as exc:
            raise ClientResponseException(
                500, str(exc), "Liftover failed. Contact the system administrator."
            ) from exc
        except Exception as exc:
            logger.error(f"Import failed (Comparison 2): {str(exc)}")
            message = (
                "Server was unable to process file import request.\n"
                "Contact the system administrator."
            )
            raise ClientResponseException(500, message) from exc

    def _import_with_context(
        self,
    ) -> tuple[Generator[EufRecord | Bed6Record, None, None], dict[str, str | int]]:
        local_context: dict[str, str | int] = {
            "eufid": "UPLOAD".ljust(Identifiers.EUFID.length)
        }
        if self._is_euf:
            try:
                euf_importer = EufImporter(
                    stream=self._tmp_file_handle, source=self._upload_name
                )
                self._validator_service.create_read_only_import_context(
                    euf_importer, self._taxa_id
                )
                context = self._validator_service.get_read_only_context()
                if context.is_liftover:
                    local_context["eufid"] = "LIFTED".ljust(Identifiers.EUFID.length)
                return (
                    self._validator_service.get_validated_records(
                        euf_importer, context
                    ),
                    local_context,
                )
            except SpecsError as exc:
                message = str(exc)
                raise ClientResponseException(
                    422,
                    message,
                    f"Invalid bedRMod format specifications: {message}\n"
                    "Modify the file and start again, or toggle BED6 on "
                    "file selection to ignore header.",
                ) from exc
            except DatasetHeaderError as exc:
                message = str(exc)
                raise ClientResponseException(
                    422,
                    message,
                    f"Inconsistent header: {message}\n"
                    "Select reference dataset for the correct organism.",
                ) from exc
            except DatasetImportError as exc:
                message = str(exc)
                raise ClientResponseException(
                    422,
                    message,
                    f"{message}\nValidate the file header for inconsistencies.",
                ) from exc
            except Exception as exc:
                logger.error(f"Import failed (Comparison 1): {str(exc)}")
                message = (
                    "Server was unable to process file import request.\n"
                    "Contact the system administrator."
                )
                raise ClientResponseException(500, message) from exc
        else:
            bed6_importer = Bed6Importer(
                stream=self._tmp_file_handle, source=self._upload_name
            )
            local_context = {**local_context, "frequency": 1, "coverage": 0}
            return bed6_importer.parse(), local_context

    def __exit__(self, exc_type, exc_value, traceback):
        if self._tmp_file_handle is not None:
            self._tmp_file_handle.close()
