from urllib.parse import quote

from scimodom.config import Config


API_PREFIX = "api/v0"  # must fit with client/public/config.js
USER_API_ROUTE = f"/{API_PREFIX}/user"
ACCESS_API_ROUTE = f"/{API_PREFIX}/access"
DATASET_API_ROUTE = f"/{API_PREFIX}/dataset"
BAM_FILE_API_ROUTE = f"/{API_PREFIX}/bam_file"
UPLOAD_API_ROUTE = f"/{API_PREFIX}/upload"
TRANSFER_API_ROUTE = f"/{API_PREFIX}/transfer"
DATA_MANAGEMENT_API_ROUTE = f"/{API_PREFIX}/management"

CONFIRM_USER_REGISTRATION_URI = "confirm_user_registration"
REQUEST_PASSWORD_RESET_URI = "request_password_reset"


def get_user_registration_link(email: str, token: str) -> str:
    return _build_link(CONFIRM_USER_REGISTRATION_URI, quote(email), token)


def get_password_reset_link(email: str, token: str) -> str:
    return _build_link(REQUEST_PASSWORD_RESET_URI, quote(email), token)


def _build_link(*parts):
    if Config.HTTP_PUBLIC_URL is None or Config.HTTP_PUBLIC_URL == "":
        raise Exception("Internal error: Required parameter PUBLIC_URL not set.")
    if Config.HTTP_PUBLIC_URL[-1] == "/":
        result_parts = [Config.HTTP_PUBLIC_URL[:-1]]
    else:
        result_parts = [Config.HTTP_PUBLIC_URL]
    for part in parts:
        result_parts.append("/")
        result_parts.append(part)
    return "".join(result_parts)
