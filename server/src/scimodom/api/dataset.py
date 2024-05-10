from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity

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
