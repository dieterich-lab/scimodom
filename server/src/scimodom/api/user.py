import logging
from datetime import timedelta
from smtplib import SMTPException

from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import NoResultFound

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    get_required_json_fields,
)
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
    """Register a new user.

    Create a new, inactive user and send out
    a token to validate the email address.

    :param request: The incoming JSON request payload
    with "email" and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 403: User exists
    :statuscode 500: SMTPException or Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "password")
        user_service.register_user(email=fields["email"], password=fields["password"])
        return jsonify({"result": "OK"})
    except ClientResponseException as exc:
        return exc.response_tuple
    except UserExists:
        return create_error_response(
            403,
            "User exists",
            "User already exists.\nTry to reset your password.",
        )
    except SMTPException as exc:
        logger.error(f"Failed to send registration email: {exc}")
        return create_error_response(
            500,
            "Failed to send registration email",
            "Failed to send registration email.\n"
            "Make sure the email address is valid.\n"
            "If the problem persists, contact the system administrator.",
        )
    except Exception:
        logger.error(f"Unexpected error while registering user '{fields['email']}'")
        return create_error_response(
            500,
            "Registration failed unexpectedly",
            "Registration failed due to an unexpected server error. "
            "No account was created; you can safely try again.\n"
            "If the problem persists, contact the system administrator.",
        )


@user_api.route("/confirm_user", methods=["POST"])
def confirm_user():
    """Activate a registered user.

    :param request: The incoming JSON request payload
    with "email" and "token".
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 401: Unauthorized (credentials failed authentication)
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "token")
        user_service.confirm_user(
            email=fields["email"], confirmation_token=fields["token"]
        )
        return jsonify({"result": "OK"})
    except ClientResponseException as exc:
        return exc.response_tuple
    except WrongUserOrPassword:
        return create_error_response(
            401, "Wrong username, wrong or expired confirmation link"
        )


@user_api.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    """Request a reset token.

    :param request: The incoming JSON request payload with "email".
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 404: Unknown user
    :statuscode 500: SMTPException or Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email")
        user_service.request_password_reset(fields["email"])
        return jsonify({"result": "OK"})
    except ClientResponseException as exc:
        return exc.response_tuple
    except NoSuchUser:
        return create_error_response(
            404,
            "Unknown user",
            "There is no user with this email address.\n"
            "Make sure this is the same address used for registration.\n"
            "If the problem persists, contact the system administrator.",
        )
    except SMTPException as exc:
        logger.error(f"Failed to send registration email: {exc}")
        return create_error_response(
            500,
            "Failed to send password reset link.",
            "Failed to send email token.\n" "Contact the system administrator.",
        )


@user_api.route("/do_password_reset", methods=["POST"])
def do_password_reset():
    """Reset password (publicly accessible).

    :param request: The incoming JSON request payload with
    "email", "token", and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 401: Unauthorized (credentials failed authentication)
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "token", "password")
        user_service.do_password_reset(
            email=fields["email"],
            confirmation_token=fields["token"],
            new_password=fields["password"],
        )
        return jsonify({"result": "OK"})
    except ClientResponseException as exc:
        return exc.response_tuple
    except WrongUserOrPassword:
        return create_error_response(
            401,
            "Wrong user, wrong, used, or expired link.",
            "There is no user with this email address, the link\n"
            "has already been used, is expired or truncated.\n"
            "Contact the system administrator.",
        )


@user_api.route("/login", methods=["POST"])
def login():
    """Login.

    :param request: The incoming JSON request payload with
    "email" and "password".
    :returns: JSON object with access token
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 401: Unauthorized (credentials failed authentication)
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "password")
        if user_service.check_password(fields["email"], fields["password"]):
            access_token = create_access_token(
                identity=fields["email"], expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
            )
            return jsonify({"access_token": access_token})
        return create_error_response(
            401, "Wrong user or password", "Wrong email address or password."
        )
    except ClientResponseException as exc:
        return exc.response_tuple


@user_api.route("/refresh_access_token")
@jwt_required()
def refresh_access_token():
    """Refresh access token.

    :param header: The request header with current
    token.
    :returns: JSON object with new access token.
    :statuscode 200: OK
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    access_token = create_access_token(
        identity=email, expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
    )
    return jsonify({"access_token": access_token})


@user_api.route("/change_password", methods=["POST"])
@jwt_required()
def change_password():
    """Change password (restricted to authenticated users).

    :param request: The request and header with current
    token and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request (malformed request body, missing fields)
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("password")
        user_service.change_password(
            email=email,
            new_password=fields["password"],
        )
        return jsonify({"result": "OK"})
    except ClientResponseException as exc:
        return exc.response_tuple


@user_api.route("/may_change_dataset/<dataset_id>", methods=["GET"])
@jwt_required()
def may_change_dataset(dataset_id):
    """Check if user has access (restricted to authenticated users).

    :param header: The request header with current token.
    :statuscode 200: OK
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    user_service = get_user_service()
    user = user_service.get_user_by_email(email)
    dataset_service = get_dataset_service()
    permission_service = get_permission_service()
    try:
        dataset = dataset_service.get_by_id(dataset_id)
    except NoResultFound:
        return create_error_response(404, "Unknown dataset")
    return {"write_access": permission_service.may_change_dataset(user, dataset)}


@user_api.route("/get_username", methods=["GET"])
@jwt_required()
def get_username():
    """Get username (restricted to authenticated users).

    :param header: The request header with current token.
    :statuscode 200: OK
    :statuscode 401: Unauthorized (expired token, missing header)
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    return jsonify(username=email), 200
