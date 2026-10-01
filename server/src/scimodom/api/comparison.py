import logging
from dataclasses import dataclass
from typing import Generator, Iterable, Sequence, TextIO

from flask import Blueprint
from pydantic import BaseModel

from scimodom.api.helpers import (
    ClientResponseException,
    get_optional_valid_dataset_id_list,
    get_optional_valid_tmp_file_id,
    get_valid_file_name,
    get_optional_bool,
    get_valid_taxa_id,
    get_response_from_pydantic_object,
)
from scimodom.services.assembly import LiftOverError
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.data import get_data_service
from scimodom.services.file import get_file_service
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

dataset_comparison_api = Blueprint("dataset_comparison_api", __name__)


MAX_DATASET_IDS_IN_LIST = 3


class IntersectResponse(BaseModel):
    """DTO for intersect records."""

    records: list[IntersectRecord]


class ClosestResponse(BaseModel):
    """DTO for closest records."""

    records: list[ClosestRecord]


class SubtractResponse(BaseModel):
    """DTO for subtract records."""

    records: list[SubtractRecord]


@dataset_comparison_api.get("/intersect")
def intersect():
    """Intersect two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :return: JSON object with JSON array of
    intersected records.
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed or missing parameters,
    invalid identifiers, too many dataset
    :statuscode 404: Not Found - dataset, file, or taxon
    :statuscode 422: Unprocessable Content - data validation
    :statuscode 500: Internal Server Error (or failed liftover)
    """
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.intersect_comparison_records(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(IntersectResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


@dataset_comparison_api.get("/closest")
def closest():
    """Intersect (non-overlap) two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :return: JSON object with JSON array of
    intersected records.
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed or missing parameters,
    invalid identifiers, too many dataset
    :statuscode 404: Not Found - dataset, file, or taxon
    :statuscode 422: Unprocessable Content - data validation
    :statuscode 500: Internal Server Error (or failed liftover)
    """
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.closest_comparison_records(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return get_response_from_pydantic_object(ClosestResponse(records=records))
    except ClientResponseException as e:
        return e.response_tuple


@dataset_comparison_api.get("/subtract")
def subtract():
    """Subtract two or more dataset.

    A "NoDataRecords" can be raised, but this
    should not happen in practice. If it does,
    it will be caught by the 500.

    :param request: The request with required
    and optional parameters.
    :return: JSON object with JSON array of
    intersected records.
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed or missing parameters,
    invalid identifiers, too many dataset
    :statuscode 404: Not Found - dataset, file, or taxon
    :statuscode 422: Unprocessable Content - data validation
    :statuscode 500: Internal Server Error (or failed liftover)
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
        self._reference_ids = get_optional_valid_dataset_id_list(
            "reference",
            MAX_DATASET_IDS_IN_LIST,
        )
        self._comparison_ids = get_optional_valid_dataset_id_list(
            "comparison",
            MAX_DATASET_IDS_IN_LIST,
        )
        self._upload_id = get_optional_valid_tmp_file_id("upload")
        self._upload_name = get_valid_file_name("uploadName")
        is_strand = get_optional_bool("strand")
        self._is_strand = True if is_strand is None else is_strand
        is_euf = get_optional_bool("euf")
        self._is_euf = False if is_euf is None else is_euf
        self._taxa_id: int | None = None
        if self._is_euf:
            try:
                self._taxa_id = get_valid_taxa_id()
            except ClientResponseException as exc:
                response, status_code = exc.response_tuple
                raise ClientResponseException(
                    status_code,
                    response["message"],
                    "Request needs a valid 'taxaId' when 'euf=true'",
                ) from exc
        self._tmp_file_handle: TextIO | None = None

        if len(self._reference_ids) == 0:
            raise ClientResponseException(
                400, "Missing required parameter: 'reference'"
            )
        if self._upload_id is None and len(self._comparison_ids) == 0:
            raise ClientResponseException(
                400, "Missing required parameter: 'upload' xor 'comparison'"
            )
        if self._upload_id is not None and len(self._comparison_ids) > 0:
            raise ClientResponseException(
                400, "Too many parameters: use 'upload' xor 'comparison'"
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
                    f"Upload file not found: {self._upload_id}"
                    "File not found. Select the file again and try to re-upload.",
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
                "Invalid bedRMod format specifications.\n"
                f"Too many skipped records: {exc.error_summary}\n"
                "Modify the file to conform to the latest bedRMod format specifications\n"
                "or toggle the BED6 option to ignore validation.",
            ) from exc
        except LiftOverError as exc:
            raise ClientResponseException(
                500, str(exc), "Liftover failed. Contact our support team."
            ) from exc
        except Exception as exc:
            logger.error(f"Import failed (Comparison 2): {exc}")
            message = (
                "The server was unable to process a file import request.\n"
                "Contact our support team."
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
                raise ClientResponseException(
                    422,
                    str(exc),
                    f"Invalid bedRMod format specifications:\n{exc}\n"
                    "Modify the file header to conform to the latest specifications\n"
                    "or toggle the BED6 option to ignore validation.",
                ) from exc
            except DatasetHeaderError as exc:
                raise ClientResponseException(
                    422,
                    str(exc),
                    f"The request form must agree with the file header:\n{exc}\n"
                    "Select reference dataset for the correct organism.",
                ) from exc
            except DatasetImportError as exc:
                raise ClientResponseException(
                    422,
                    str(exc),
                    f"Validate the file header for inconsistencies: {exc}",
                ) from exc
            except Exception as exc:
                logger.error(f"Import failed (Comparison 1): {exc}")
                message = (
                    "The server was unable to process a file import request.\n"
                    "Contact our support team."
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
