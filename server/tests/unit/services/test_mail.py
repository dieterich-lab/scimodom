from urllib.parse import quote

import pytest
from unittest.mock import call

from scimodom.services.mail import MailService


class FakeUrlService:
    @staticmethod
    def get_user_registration_link(email: str, token: str) -> str:
        return FakeUrlService._build_link("REGISTRATION_URI", quote(email), token)

    @staticmethod
    def get_password_reset_link(email: str, token: str) -> str:
        return FakeUrlService._build_link("PWD_RESET_URI", quote(email), token)

    def _build_link(*parts):
        result_parts = []
        for part in parts:
            result_parts.append("/")
            result_parts.append(part)
        return "".join(result_parts)


@pytest.fixture
def mail_service():
    yield MailService(
        url_service=FakeUrlService(),
        smtp_server="server.mail.com",
        from_address="from@address.com",
        notification_address="notification@address.com",
    )


@pytest.fixture
def mock_smtp(mocker):
    mock_SMTP = mocker.MagicMock(name="scimodom.services.mail.smtplib.SMTP")
    mocker.patch("scimodom.services.mail.smtplib.SMTP", new=mock_SMTP)
    return mock_SMTP


# tests


def test_send_register_confirmation_token(mail_service, mock_smtp):
    expected_call = call(
        "from@address.com",
        "user@email.com",
        'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: Sci-ModoM - Confirm your email\nFrom: from@address.com\n\n\nPlease verify your email user@email.com to complete registration by clicking this link\n\n        /REGISTRATION_URI/user%40email.com/XXX\n\nIf you didn\'t create an account, please ignore this message and consider reporting the incident to from@address.com.\n',
    )
    mail_service.send_register_confirmation_token("user@email.com", "XXX")
    assert mock_smtp.return_value.sendmail.call_count == 1
    assert mock_smtp.return_value.sendmail.mock_calls[0] == expected_call


def test_send_password_reset_token(mail_service, mock_smtp):
    expected_call = call(
        "from@address.com",
        "user@email.com",
        'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: Sci-ModoM - Reset your password\nFrom: from@address.com\n\n\nA new password request was made for user@email.com.\nIf this was you, click this link\n\n        /PWD_RESET_URI/user%40email.com/XXX\n\nIf you didn\'t request a new password, please ignore this message and\nconsider reporting the incident to from@address.com.\n',
    )
    mail_service.send_password_reset_token("user@email.com", "XXX")
    assert mock_smtp.return_value.sendmail.call_count == 1
    assert mock_smtp.return_value.sendmail.mock_calls[0] == expected_call


def test_send_project_request_notification(mail_service, mock_smtp):
    expected_call = call(
        "from@address.com",
        "notification@address.com",
        'Content-Type: text/plain; charset="us-ascii"\nMIME-Version: 1.0\nContent-Transfer-Encoding: 7bit\nSubject: Sci-ModoM - New project request received\nFrom: from@address.com\n\nProject: UUID',
    )
    mail_service.send_project_request_notification("UUID")
    assert mock_smtp.return_value.sendmail.call_count == 1
    assert mock_smtp.return_value.sendmail.mock_calls[0] == expected_call
