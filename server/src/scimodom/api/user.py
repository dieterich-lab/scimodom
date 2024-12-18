import logging
from datetime import timedelta
from smtplib import SMTPException

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import create_error_response
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
        return create_error_response(
            403,
            "User exists",
            "User already exists.\nTry to reset your password.",
        )
    except SMTPException as e:
        logger.error(f"Failed to send registration email: {e}")
        return create_error_response(
            500,
            "Failed to send registration email",
            "Failed to send registration email.\n"
            "Make sure the email address is valid.\n"
            "If the problem persists, contact the system administrator.",
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
        return create_error_response(
            400, "Bad confirmation link", "Bad confirmation link"
        )


@user_api.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    user_service = get_user_service()
    try:
        user_service.request_password_reset(request.json["email"])
    except NoSuchUser:
        return create_error_response(
            404,
            "Unknown user",
            "There is no user with this email address.\n"
            "Make sure this is the same address used for registration.\n"
            "If the problem persists, contact the system administrator.",
        )
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
        return create_error_response(
            401,
            "Wrong token",
            "Sorry we don't recognise the link - you might have truncated it.\n"
            "If not, please contact the system administrator.",
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
        return create_error_response(
            401, "Wrong user or password", "Wrong email address or password."
        )


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
        return create_error_response(404, "No such user")
    try:
        dataset = dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        return create_error_response(404, "Unknown dataset")

    return {"write_access": permission_service.may_change_dataset(user, dataset)}


@user_api.route("/get_username", methods=["GET"])
@jwt_required()
def get_username():
    email = get_jwt_identity()
    return jsonify(username=email), 200
