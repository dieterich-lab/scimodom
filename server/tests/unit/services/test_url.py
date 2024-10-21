import pytest

from scimodom.services.url import UrlService


@pytest.fixture
def url_service(Session):
    yield UrlService(http_public_url="my-url.com/")


def test_get_user_registration_link(url_service):
    expected_url = "my-url.com/confirm_user_registration/x%40example.com/XXX"
    assert (
        url_service.get_user_registration_link(email="x@example.com", token="XXX")
        == expected_url
    )


def test_get_password_reset_link(url_service):
    expected_url = "my-url.com/request_password_reset/x%40example.com/XXX"
    assert (
        url_service.get_password_reset_link(email="x@example.com", token="XXX")
        == expected_url
    )
