import logging

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity

logger = logging.getLogger(__name__)

access_api = Blueprint("access_api", __name__)


@access_api.route("/testlogin", methods=["GET"])
@cross_origin(supports_credentials=True)
@jwt_required()
def testlogin():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200