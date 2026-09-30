import logging
from datetime import timedelta
from smtplib import SMTPException

from flask import Blueprint
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

from scimodom.api.helpers import (
    ClientResponseException,
    create_error_response,
    get_required_json_fields,
)
from scimodom.services.user import (
    get_user_service,
    UserExists,
    WrongUserOrPassword,
    NoSuchUser,
)

logger = logging.getLogger(__name__)

user_api = Blueprint("user_api", __name__)

ACCESS_TOKEN_EXPIRATION_TIME = timedelta(hours=2)


@user_api.post("/users")
def register_user():
    """Register a new user.

    Create a new, inactive user and send out
    a token to validate the email address.
    Confirmation is handled by a frontend route
    via CONFIRM_USER_REGISTRATION_URI.

    :param request: The incoming JSON request payload
    with "email" and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request - request body, missing fields
    :statuscode 409: Conflict - user exists
    :statuscode 500: Internal Server Error (or SMTPException)
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "password")
        user_service.register_user(email=fields["email"], password=fields["password"])
        return {"message": "OK"}, 200
    except ClientResponseException as exc:
        return exc.response_tuple
    except UserExists as exc:
        return create_error_response(
            409,
            str(exc),
            "User already exists. Try to reset your password.",
        )
    except SMTPException as exc:
        logger.error(f"Failed to send registration email: {exc}")
        return create_error_response(
            500,
            str(exc),
            "Failed to send registration email. Please verify your email address.\n"
            "If the problem persists, contact our support team.",
        )


@user_api.post("/users/confirmation")
def confirm_user_registration():
    """Activate a registered user.

    Provide an API route for user confirmation.
    The other route is via the frontend
    CONFIRM_USER_REGISTRATION_URI, cf. /users

    :param request: The incoming JSON request payload
    with "email" and "token".
    :statuscode 200: OK
    :statuscode 400: Bad request - request body, missing fields
    :statuscode 401: Unauthorized - credentials
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "token")
        user_service.confirm_user(
            email=fields["email"], confirmation_token=fields["token"]
        )
        return {"message": "OK"}, 200
    except ClientResponseException as exc:
        return exc.response_tuple
    except WrongUserOrPassword:
        return create_error_response(401, "Invalid credentials")


@user_api.post("/users/password/request")
def request_password_reset():
    """Request a reset token.

    Send out a reset token. The request is handled
    by a frontend route via REQUEST_PASSWORD_RESET_URI,
    which in turns triggers a call to /users/password/reset
    via a FE dialog.

    :param request: The incoming JSON request payload with "email".
    :statuscode 200: OK
    :statuscode 400: Bad request - request body, missing fields
    :statuscode 404: Not Found - user
    :statuscode 500: Internal Server Error (or SMTPException)
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email")
        user_service.request_password_reset(fields["email"])
        return {"message": "OK"}, 200
    except ClientResponseException as exc:
        return exc.response_tuple
    except NoSuchUser:
        return create_error_response(
            404,
            f'User \'{fields["email"]}\' not found',
            "User not found. Please verify your email address.\n"
            "If the problem persists, contact our support team.",
        )
    except SMTPException as exc:
        logger.error(f"Failed to send registration email: {exc}")
        return create_error_response(
            500,
            str(exc),
            "Failed to send email. Please verify your email address.\n"
            "If the problem persists, contact our support team.",
        )


@user_api.post("/users/password/reset")
def do_password_reset():
    """Reset password.

    :param request: The incoming JSON request payload with
    "email", "token", and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed request body, missing fields
    :statuscode 401: Unauthorized - credentials
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
        return {"message": "OK"}, 200
    except ClientResponseException as exc:
        return exc.response_tuple
    except WrongUserOrPassword:
        return create_error_response(401, "Invalid credentials")


@user_api.get("/users/me")
@jwt_required()
def get_my_username():
    """Get username for an authenticated users.

    :param header: The request header with current token.
    :statuscode 200: OK
    :statuscode 401: Unauthorized - expired token, missing header
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    return {"email": email}, 200


@user_api.put("/users/me/password")
@jwt_required()
def change_my_password():
    """Change password for an authenticated user.

    :param request: The request and header with current
    "token" and "password".
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed request body, missing fields
    :statuscode 401: Unauthorized - expired token, missing header
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
        return {"message": "OK"}, 200
    except ClientResponseException as exc:
        return exc.response_tuple


@user_api.post("/sessions")
def login():
    """Login.

    :param request: The incoming JSON request payload with
    "email" and "password".
    :return: JSON object with access token
    :statuscode 200: OK
    :statuscode 400: Bad request - malformed request body, missing fields
    :statuscode 401: Unauthorized - credentials
    :statuscode 500: Internal Server Error
    """
    user_service = get_user_service()
    try:
        fields = get_required_json_fields("email", "password")
        if user_service.check_password(fields["email"], fields["password"]):
            access_token = create_access_token(
                identity=fields["email"], expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
            )
            return {"access_token": access_token}, 200
        return create_error_response(401, "Invalid credentials")
    except ClientResponseException as exc:
        return exc.response_tuple


@user_api.post("/sessions/refresh")
@jwt_required()
def refresh_access_token():
    """Refresh access token.

    :param header: The request header with current
    token.
    :return: JSON object with new access token.
    :statuscode 200: OK
    :statuscode 401: Unauthorized - expired token, missing header
    :statuscode 422: Unprocessable Content (not enough segments,
    signature verification failed)
    :statuscode 500: Internal Server Error
    """
    email = get_jwt_identity()
    access_token = create_access_token(
        identity=email, expires_delta=ACCESS_TOKEN_EXPIRATION_TIME
    )
    return {"access_token": access_token}, 200
