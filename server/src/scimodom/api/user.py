from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from scimodom.services.user import (
    get_user_service,
    UserExists,
    WrongUserOrPassword,
    NoSuchUser,
)

user_api = Blueprint("api_user", __name__)


@user_api.route("/register_user", methods=["POST"])
def register_user():
    user_service = get_user_service()
    try:
        user_service.register_user(
            email=request.json("email"), password=request.json("password")
        )
        return jsonify({"result": "OK"})

    except UserExists:
        return jsonify({"result": "User exists"}), 403


@user_api.route("/confirm_user", methods=["POST"])
def confirm_user():
    user_service = get_user_service()
    try:
        user_service.confirm_user(
            email=request.json("email"), confirmation_token=request.json("token")
        )
        return jsonify({"result": "OK"})
    except WrongUserOrPassword:
        return jsonify({"result": "Bad confirmation link"}), 400


@user_api.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    user_service = get_user_service()
    try:
        user_service.request_password_reset(request.json("email"))
    except NoSuchUser:
        return jsonify({"result": "Unknown user"}), 404
    return jsonify({"result": "OK"})


@user_api.route("/do_password_reset", methods=["POST"])
def do_password_reset():
    user_service = get_user_service()
    try:
        user_service.do_password_reset(
            email=request.json("email"),
            confirmation_token=request.json("token"),
            new_password=request.json("password"),
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
        access_token = create_access_token(identity=email)
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"result": "Wrong user or password"}), 401


@user_api.route("/refresh_access_token")
@jwt_required()
def refresh_access_token():
    email = get_jwt_identity()
    access_token = create_access_token(identity=email)
    return jsonify({"access_token": access_token})
