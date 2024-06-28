from functools import cache
from urllib.parse import quote

from scimodom.config import get_config


API_PREFIX = "api/v0"  # must fit with client/public/config.js
BAM_FILE_API_ROUTE = f"/{API_PREFIX}/bam_file"
DATA_MANAGEMENT_API_ROUTE = f"/{API_PREFIX}/management"
DATASET_API_ROUTE = f"/{API_PREFIX}/dataset"
MODIFICATION_API_ROUTE = f"/{API_PREFIX}/modification"
PROJECT_API_ROUTE = f"/{API_PREFIX}/project"
TRANSFER_API_ROUTE = f"/{API_PREFIX}/transfer"
USER_API_ROUTE = f"/{API_PREFIX}/user"

CONFIRM_USER_REGISTRATION_URI = "confirm_user_registration"
REQUEST_PASSWORD_RESET_URI = "request_password_reset"


class UrlService:
    def __init__(self, http_public_url: str):
        if http_public_url[-1] == "/":
            http_public_url = http_public_url[:-1]
        self._http_public_url = http_public_url

    def get_user_registration_link(self, email: str, token: str) -> str:
        return self._build_link(CONFIRM_USER_REGISTRATION_URI, quote(email), token)

    def get_password_reset_link(self, email: str, token: str) -> str:
        return self._build_link(REQUEST_PASSWORD_RESET_URI, quote(email), token)

    def _build_link(self, *parts):
        result_parts = [self._http_public_url]
        for part in parts:
            result_parts.append("/")
            result_parts.append(part)
        return "".join(result_parts)


@cache
def get_url_service():
    return UrlService(http_public_url=get_config().HTTP_PUBLIC_URL)
