import logging
from dataclasses import dataclass
from typing import Iterable

from flask import Blueprint, Response
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import BaseModel

from scimodom.api.helpers import (
    get_valid_dataset_id_list_from_request_parameter,
    get_valid_tmp_file_id_from_request_parameter,
    get_valid_boolean_from_request_parameter,
    ClientResponseException,
)
from scimodom.services.bedtools import get_bedtools_service, BedToolsService
from scimodom.services.dataset import get_dataset_service
from scimodom.services.file import get_file_service
from scimodom.services.data import get_data_service
from scimodom.services.user import get_user_service
from scimodom.utils.bed_importer import Bed6Importer, EufImporter
from scimodom.utils.bedtools_dto import (
    IntersectRecord,
    ClosestRecord,
    SubtractRecord,
    ComparisonRecord,
)

logger = logging.getLogger(__name__)

dataset_api = Blueprint("dataset_api", __name__)


@dataset_api.route("/list_all", methods=["GET"])
def list_all():
    dataset_service = get_dataset_service()
    return dataset_service.get_datasets()


@dataset_api.route("/list_mine", methods=["GET"])
@jwt_required()
def list_mine():
    user_service = get_user_service()
    dataset_service = get_dataset_service()
    email = get_jwt_identity()
    user = user_service.get_user_by_email(email)
    return dataset_service.get_datasets(user)


class IntersectResponse(BaseModel):
    records: list[IntersectRecord]


@dataset_api.route("/intersect", methods=["GET"])
@cross_origin(supports_credentials=True)
def intersect():
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.intersect(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return _get_response_from_pydantic_object(
                IntersectResponse(records=records)
            )
    except ClientResponseException as e:
        return e.response_tupel


class _CompareContext:
    @dataclass
    class Ctx:
        bedtools_service: BedToolsService
        a_records: Iterable[ComparisonRecord]
        b_records_list: list[Iterable[ComparisonRecord]]
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
        self._is_strand = get_valid_boolean_from_request_parameter(
            "strand", default=False
        )
        self._is_euf = get_valid_boolean_from_request_parameter("is_euf", default=False)
        self._tmp_file_handle = None

        if self._upload_id is None and len(self._comparison_ids) == 0:
            raise ClientResponseException(
                400, "Need either a upload_id or a comparison_ids"
            )
        if self._upload_id is not None and len(self._comparison_ids) > 0:
            raise ClientResponseException(
                400, "Can only handle upload_id or comparison_ids, but not both"
            )
        self._data_service = get_data_service()

    def __enter__(self) -> Ctx:
        if self._upload_id is None:
            # Unfortunately the MySQL driver does not allow use to have multiple queries run at once.
            # To work around this issue we have to buffer the b_records in memory
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
            except FileNotFoundError:
                raise ClientResponseException(
                    404, "Your uploaded file was not found - maybe it expired"
                )
            b_records_list = [list(self._get_comparison_records_from_file())]

        a_records = self._get_comparison_records_from_db(self._reference_ids)
        return self.Ctx(
            bedtools_service=get_bedtools_service(),
            a_records=a_records,
            b_records_list=b_records_list,
            is_strand=self._is_strand,
        )

    def _get_comparison_records_from_db(self, dataset_ids):
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

    def _get_comparison_records_from_file(self):
        if self._is_euf:
            for x in EufImporter(stream=self._tmp_file_handle).parse():
                raw_record = x.model_dump()
                yield ComparisonRecord(eufid="upload      ", **raw_record)
        else:
            for x in Bed6Importer(stream=self._tmp_file_handle).parse():
                raw_record = x.model_dump()
                yield ComparisonRecord(
                    eufid="upload      ", frequency=0, coverage=0, **raw_record
                )

    def __exit__(self, exc_type, exc_value, traceback):
        if self._tmp_file_handle is not None:
            self._tmp_file_handle.close()


def _get_response_from_pydantic_object(obj: BaseModel):
    return Response(response=obj.json(), status=200, mimetype="application/json")


class ClosestResponse(BaseModel):
    records: list[ClosestRecord]


@dataset_api.route("/closest", methods=["GET"])
@cross_origin(supports_credentials=True)
def closest():
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.closest(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return _get_response_from_pydantic_object(ClosestResponse(records=records))
    except ClientResponseException as e:
        return e.response_tupel


class SubtractResponse(BaseModel):
    records: list[SubtractRecord]


@dataset_api.route("/subtract", methods=["GET"])
@cross_origin(supports_credentials=True)
def subtract():
    try:
        with _CompareContext() as ctx:
            records = ctx.bedtools_service.subtract(
                ctx.a_records, ctx.b_records_list, is_strand=ctx.is_strand
            )
            return _get_response_from_pydantic_object(SubtractResponse(records=records))
    except ClientResponseException as e:
        return e.response_tupel
