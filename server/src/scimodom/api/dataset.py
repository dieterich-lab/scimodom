from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

from scimodom.services.comparison import get_comparison_service
from scimodom.services.dataset import get_dataset_service
from scimodom.services.user import get_user_service

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


@dataset_api.route("/compare", methods=["GET"])
@cross_origin(supports_credentials=True)
def compare():
    """Compare dataset (Compare View)."""
    reference_ids = request.args.getlist("reference", type=str)
    comparison_ids = request.args.getlist("comparison", type=str)
    upload_path = request.args.get("upload", type=str)
    query_operation = request.args.get("operation", type=str)
    print(f"{reference_ids}, {comparison_ids}, {upload_path}, {query_operation}")

    # TODO
    is_euf = True

    operation, strand = query_operation.split("S")
    comparison_service = get_comparison_service(operation, eval(strand))

    if upload_path:
        # try:
        comparison_service.upload_records(upload_path, is_euf)
        # except:  # FileNotFoundError, FailedUploadError, NoRecordsFoundError
        #    pass
    else:
        # try:
        comparison_service.query_comparison_records(comparison_ids)
        # except:  # NoRecordsFoundErrror - querying from FE this will not occur...
        #    pass
    comparison_service.query_reference_records(reference_ids)
    # try:
    return comparison_service.compare_dataset()
    # print(f"API {tata[:2]}")
    # return tata
    # except: # what errors pybedtools can rise here?
    #    return jsonify({"message": "Failed"}), 400
