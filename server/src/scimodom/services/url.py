from functools import cache
from urllib.parse import quote

from scimodom.config import get_config


API_PREFIX = "api/v0"
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
    """Utility class to construct valid URLs.

    :param http_public_url: Application URL
    :type http_public_url: str
    """

    def __init__(self, http_public_url: str):
        if http_public_url[-1] == "/":
            http_public_url = http_public_url[:-1]
        self._http_public_url = http_public_url

    def get_user_registration_link(self, email: str, token: str) -> str:
        """Construct registration link.

        :param email: User email
        :type email: str
        :param token: Token
        :type token: str
        :returns: Registration link
        :rtype: str
        """
        return self._build_link(CONFIRM_USER_REGISTRATION_URI, quote(email), token)

    def get_password_reset_link(self, email: str, token: str) -> str:
        """Construct password reset link.

        :param email: User email
        :type email: str
        :param token: Token
        :type token: str
        :returns: Password reset link
        :rtype: str
        """
        return self._build_link(REQUEST_PASSWORD_RESET_URI, quote(email), token)

    def _build_link(self, *parts):
        result_parts = [self._http_public_url]
        for part in parts:
            result_parts.append("/")
            result_parts.append(part)
        return "".join(result_parts)


@cache
def get_url_service():
    """Provide a helper function to set up an UrlService.

    :returns: URL service instance
    :rtype: UrlService
    """
    return UrlService(http_public_url=get_config().HTTP_PUBLIC_URL)
