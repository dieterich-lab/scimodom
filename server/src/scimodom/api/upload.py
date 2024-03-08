import logging

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

upload_api = Blueprint("upload_api", __name__)


@upload_api.route("/upload", methods=["GET"])
@cross_origin(supports_credentials=True)
@jwt_required()
def secure_endpoint():
    pass
