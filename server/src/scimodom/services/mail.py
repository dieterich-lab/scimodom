from email.mime.text import MIMEText
from smtplib import SMTP
from typing import Optional

from scimodom.config import Config
from scimodom.utils.url_routes import (
    get_user_registration_link,
    get_password_reset_link,
)


class MailService:
    """Server to handle email notifications. For now all email
    templates are hardcoded in English.

    :param smtp_server: A server willing to relay unauthenticated emails for us.
    :type smtp_server: str
    :param from_address: The email address used for the sender. It must be also acceptable
    for the SMTP server.
    :type from_address: str
    """

    def __init__(self, smtp_server: str, from_address: str):
        self._smtp_server = smtp_server
        self._from_address = from_address

    def _send(self, to_address, subject: str, text: str):
        """
        Sends email template.

        :param to_address: Email address
        :type to_address: str
        :param subject: Subject
        :type subject: str
        :param text: Content
        :type text: str
        """
        connection = SMTP(self._smtp_server)
        m = MIMEText(text, "plain")
        m["Subject"] = subject
        m["From"] = self._from_address
        try:
            connection.sendmail(self._from_address, to_address, m.as_string())
        finally:
            connection.quit()

    def send_register_confirmation_token(self, email: str, token: str):
        """Sends out a message to verify the email address for
        user registration.

        :param email: Email address
        :type email: str
        :param token: Token
        :type token: str
        """
        link = get_user_registration_link(email, token)
        self._send(
            to_address=email,
            subject="Sci-ModoM - Confirm your email",
            text=f"""
Please verify your email {email} to complete registration by clicking this link

        {link}

If you didn't create an account, please ignore this message and consider reporting the incident to {self._from_address}.
""",
        )

    def send_password_reset_token(self, email: str, token: str):
        """Sends out a message to allow the user to confirm a password reset.

        :param email: Email address
        :type email: str
        :param token: Token
        :type token: str
        """
        link = get_password_reset_link(email, token)
        self._send(
            to_address=email,
            subject="Sci-ModoM - Reset your password",
            text=f"""
A new password request was made for {email}.
If this was you, click this link

        {link}

If you didn't request a new password, please ignore this message and consider reporting the incident to {self._from_address}.
""",
        )

    def send_project_request_notification(self, uuid: str):
        """Notify aministrator of a new project submission.

        :param uuid: Project temporary identifier
        :type uuid: str
        """
        self._send(
            to_address=Config.SMTP_TO_ADDRESS,
            subject="Sci-ModoM - New project request received",
            text=f"""Project template: {uuid}.json""",
        )


_cached_mail_service: Optional[MailService] = None


def get_mail_service() -> MailService:
    """
    Helper function to create a MailService by validating and injecting the configuration.

    :returns: Mail service instance
    :rtype: MailService
    """
    global _cached_mail_service
    if _cached_mail_service is None:
        for required_parameter in ["SMTP_SERVER", "SMTP_FROM_ADDRESS"]:
            value = getattr(Config, required_parameter)
            if value is None or value == "":
                raise Exception(
                    f"Internal error: Required parameter '{required_parameter}' not set"
                )

        _cached_mail_service = MailService(
            smtp_server=Config.SMTP_SERVER,
            from_address=Config.SMTP_FROM_ADDRESS,
        )
    return _cached_mail_service
