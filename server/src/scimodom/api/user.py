import logging
from datetime import timedelta
from smtplib import SMTPException

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.services.dataset import get_dataset_service
from scimodom.services.permission import get_permission_service
from scimodom.services.user import (
    get_user_service,
    UserExists,
    WrongUserOrPassword,
    NoSuchUser,
)

logger = logging.getLogger(__name__)

user_api = Blueprint("user_api", __name__)

ACCESS_TOKEN_EXPIRATION_TIME = timedelta(hours=2)


@user_api.route("/register_user", methods=["POST"])
def register_user():
    user_service = get_user_service()
    try:
        user_service.register_user(
            email=request.json["email"], password=request.json["password"]
        )
        return jsonify({"result": "OK"})

    except UserExists:
        return jsonify({"result": "User exists"}), 403
    except SMTPException as e:
        logger.error(f"Failed to sent out email: {e}")
        return (
            jsonify(
                {
                    "result": "Failed to sent out registration email - please tak to the administrator"
                }
            ),
            500,
        )


@user_api.route("/confirm_user", methods=["POST"])
def confirm_user():
    user_service = get_user_service()
    try:
        user_service.confirm_user(
            email=request.json["email"], confirmation_token=request.json["token"]
        )
        return jsonify({"result": "OK"})
    except WrongUserOrPassword:
        return jsonify({"result": "Bad confirmation link"}), 400


@user_api.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    user_service = get_user_service()
    try:
        user_service.request_password_reset(request.json["email"])
    except NoSuchUser:
        return jsonify({"result": "Unknown user"}), 404
    return jsonify({"result": "OK"})


@user_api.route("/do_password_reset", methods=["POST"])
def do_password_reset():
    user_service = get_user_service()
    try:
        user_service.do_password_reset(
            email=request.json["email"],
            confirmation_token=request.json["token"],
            new_password=request.json["password"],
        )
    except WrongUserOrPassword:
        return (
            jsonify({"result": "Something is wrong - did you have the right link?"}),
            401,
        )
    return jsonify({"result": "OK"})


@user_api.route("/login", methods=["POST"])
def login():
    user_service = get_user_service()
    email = request.json["email"]
    password = request.json["password"]
    if user_service.check_password(email, password):
        access_token = create_access_token(
            identity=email, expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
        )
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"result": "Wrong user or password"}), 401


@user_api.route("/refresh_access_token")
@jwt_required()
def refresh_access_token():
    email = get_jwt_identity()
    access_token = create_access_token(
        identity=email, expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
    )
    return jsonify({"access_token": access_token})


@user_api.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    email = get_jwt_identity()
    user_service = get_user_service()
    user_service.change_password(
        email=email,
        new_password=request.json["password"],
    )
    return jsonify({"result": "OK"})


@user_api.route("/may_change_dataset/<dataset_id>", methods=["GET"])
@jwt_required()
def may_change_dataset(dataset_id):
    email = get_jwt_identity()

    user_service = get_user_service()
    dataset_service = get_dataset_service()
    permission_service = get_permission_service()

    try:
        user = user_service.get_user_by_email(email)
    except NoSuchUser:
        return {"message": "No such user"}, 404
    try:
        dataset = dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        return {"message": "Unknown dataset"}, 404

    return {"write_access": permission_service.may_change_dataset(user, dataset)}


@user_api.route("/get_username", methods=["GET"])
@jwt_required()
def get_username():
    email = get_jwt_identity()
    return jsonify(username=email), 200
