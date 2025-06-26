"""Provide exception and error constructors."""


class ClientResponseException(Exception):
    """Extend the base exception for a client response.

    The message is meant for debugging, logging or for users
    using the REST API directly. The web frontend may fall back
    to use this message if no 'user_message' was supplied, in which
    case it is the responsibility of the frontend to add context.

    The user_message (optional) is mostly intended for user errors
    (e.g. wrong password, bad email address). This message should
    add context; the frontend will usually display it directly to
    the user without adding any context. The user_message should
    be formatted.
    """

    def __init__(
        self,
        http_status: int,
        message: str,
        user_message: str | None = None,
    ):
        super(ClientResponseException, self).__init__(
            f"HTTP status {http_status} {message}"
        )
        self.response_tuple = create_error_response(
            http_status,
            message,
            user_message,
        )


class FileTooLargeException(ClientResponseException):
    """Extend ClientResponseException for file size."""

    def __init__(self, max_size: int):
        message = _get_file_too_large_message(max_size)
        super(FileTooLargeException, self).__init__(413, message, message)


def create_error_response(
    status_code: int, message: str, user_message: str | None = None
) -> tuple[dict[str, str], int]:
    """Construct an error response.

    This function allows to generate a response in the same
    format without raising a ClientResponseException.

    :param status_code: HTTP status code
    :param message: General error message
    :param user_message: Error message specifically for the user.
    :return: Error response tuple
    """
    json_response = {"message": message}
    if user_message is not None:
        json_response["user_message"] = user_message
    return json_response, status_code


def create_file_too_large_response(max_size: int) -> tuple[dict[str, str], int]:
    """Construct an error response for file size.

    :param max_size: Allowed max. file size
    :return: Error response
    """
    message = _get_file_too_large_message(max_size)
    return create_error_response(413, message, message)


def _get_file_too_large_message(max_size: int):
    return f"File too large (max. {max_size} bytes)"


def _invalid_choice(name: str, raw: str, allowed: str) -> None:
    raise ClientResponseException(
        400, f"Invalid value for '{name}' (allowed: {allowed}, got: '{raw}')"
    )
