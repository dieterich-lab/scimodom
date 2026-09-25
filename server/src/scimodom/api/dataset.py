import logging

from flask import Blueprint, Response, request, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from pydantic import ValidationError

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    parse_valid_rna_type,
    validate_project_write_permission,
)
from scimodom.services.annotation import AnnotationService
from scimodom.services.assembly import LiftOverError
from scimodom.services.dataset import get_dataset_service
from scimodom.services.exporter import get_exporter, NoSuchDataset
from scimodom.services.file import get_file_service
from scimodom.services.sunburst import get_sunburst_service
from scimodom.services.user import get_user_service
from scimodom.services.validator import (
    SpecsError,
    DatasetHeaderError,
    DatasetImportError,
    SelectionNotFoundError,
    DatasetExistsError,
)
from scimodom.utils.importer.bed_importer import (
    BedImportTooManyErrors,
    BedImportEmptyFile,
)
from scimodom.utils.dtos.dataset import DatasetPostRequest

logger = logging.getLogger(__name__)

dataset_api = Blueprint("dataset_api", __name__)


@dataset_api.get("/datasets")
def get_datasets():
    """Get all datasets.

    :return: JSON array with all available dataset
    and related metadata.
    :statuscode 200: OK
    :statuscode 500: Internal Server Error
    """
    dataset_service = get_dataset_service()
    return dataset_service.get_datasets()


@dataset_api.post("/datasets")
@jwt_required()
def add_dataset():
    """Post a new dataset to a project and import data.

    This function looks for a dataset file under UPLOAD_PATH.

    :param request: The incoming JSON request payload
    satisfying the DatasetPostRequest model
    :statuscode 200: OK
    :statuscode 400: Bad request - model validation
    :statuscode 401: Missing Authorization Header
    :statuscode 403: Forbidden - project permission
    :statuscode 404: Not found - RNA type or selection
    :statuscode 409: Conflict - dataset exists
    :statuscode 422: Unprocessable Content - data validation,
    not enough segments, or signature verification failed
    :statuscode 500: Internal Server Error (or failed liftover)
    :statuscode 501: Not Implemented - RNA type annotation
    """
    try:
        dataset_form = DatasetPostRequest.model_validate_json(request.get_data())
        validate_project_write_permission(dataset_form.smid)
        _import_dataset(dataset_form)
    except ValidationError:
        return create_error_response(
            400,
            "Request body validation: malformed and/or bad/missing fields",
        )
    except ClientResponseException as exc:
        return exc.response_tuple

    sunburst_service = get_sunburst_service()
    sunburst_service.trigger_background_update()
    return {"message": "OK"}, 200


@dataset_api.get("/datasets/<dataset_id>/bedrmod")
def export_dataset(dataset_id: str):
    """Export a dataset in bedRMod format.

    :param dataset_id: Dataset identifier (EUFID)
    :statuscode 200: OK
    :statuscode 404: Dataset not found
    :statuscode 500: Internal Server Error
    """
    exporter = get_exporter()
    try:
        file_name = exporter.get_dataset_file_name(dataset_id)
        return Response(
            stream_with_context(exporter.generate_dataset(dataset_id)),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{file_name}"'},
        )
    except NoSuchDataset as exc:
        return create_error_response(404, str(exc))


@dataset_api.get("/users/me/datasets")
@jwt_required()
def get_my_datasets():
    """Get dataset associated with user.

    :param header: The request header with current token.
    :return: JSON array with all available dataset
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


def _import_dataset(dataset_form):
    file_service = get_file_service()
    try:
        # MS14
        rna_type = parse_valid_rna_type(dataset_form.rna_type)
        annotation_source = AnnotationService.get_annotation_source(rna_type)

        file_id = dataset_form.file_id
        if not file_service.check_tmp_upload_file_id(file_id):
            raise ClientResponseException(
                404,
                f"File '{file_id}' not found",
                "Select the file again and/or try to re-upload",
            )
    except NotImplementedError:
        raise ClientResponseException(
            501,
            f"rna_type '{rna_type}' not implemented",
        )

    dataset_service = get_dataset_service()
    try:
        with file_service.open_tmp_upload_file_by_id(file_id) as fh:
            dataset_service.import_dataset(
                fh,
                source=file_id,
                smid=dataset_form.smid,
                title=dataset_form.title,
                assembly_id=dataset_form.assembly_id,
                modification_ids=dataset_form.modification_id,
                organism_id=dataset_form.organism_id,
                technology_id=dataset_form.technology_id,
                annotation_source=annotation_source,
            )
    except ValueError:
        raise ClientResponseException(
            400,
            "Rename the file and try to re-upload",
        )
    except SelectionNotFoundError as exc:
        raise ClientResponseException(
            404,
            str(exc),
            "Invalid combination of modification(s), organism, and/or technology.\n"
            "Modify the request form to match a valid selection for this dataset.\n"
            "Use GET /catalogs/selections for valid combinations.",
        )
    except DatasetExistsError as exc:
        raise ClientResponseException(409, str(exc))
    except DatasetImportError as exc:
        raise ClientResponseException(
            422,
            str(exc),
            "Modify the request form and re-submit",
        )
    except DatasetHeaderError as exc:
        raise ClientResponseException(
            422,
            str(exc),
            "The request form must agree with the file header.\n"
            "Modify the request form or select the correct dataset to upload.",
        )
    except SpecsError as exc:
        raise ClientResponseException(
            422,
            str(exc),
            "Invalid bedRMod format specifications.\n"
            "Modify the file header to conform to the latest specifications.",
        )
    except BedImportEmptyFile as exc:
        raise ClientResponseException(
            422, str(exc), "File upload failed. The file is empty."
        )
    except BedImportTooManyErrors as exc:
        raise ClientResponseException(
            422,
            str(exc.error_summary),
            "Invalid bedRMod format specifications.\n"
            "Consult the documentation (Dataset upload errors) for more information.",
        )
    except LiftOverError as exc:
        raise ClientResponseException(
            500, str(exc), "Liftover failed. Contact the system administrator."
        )
