from email.mime.text import MIMEText
from functools import cache
import smtplib

from scimodom.config import get_config
from scimodom.services.url import UrlService, get_url_service


class MailService:
    """Server to handle email notifications. For now all email
    templates are hardcoded in English.

    :param smtp_server: A server willing to relay unauthenticated emails for us.
    :type smtp_server: str
    :param from_address: The email address used for the sender. It must be also acceptable
    for the SMTP server.
    :type from_address: str
    """

    def __init__(
        self,
        url_service: UrlService,
        smtp_server: str,
        from_address: str,
        notification_address: str,
    ):
        self._url_service = url_service
        self._smtp_server = smtp_server
        self._from_address = from_address
        self._notification_address = notification_address

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
        connection = smtplib.SMTP(self._smtp_server)
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
        link = self._url_service.get_user_registration_link(email, token)
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
        link = self._url_service.get_password_reset_link(email, token)
        self._send(
            to_address=email,
            subject="Sci-ModoM - Reset your password",
            text=f"""
A new password request was made for {email}.
If this was you, click this link

        {link}

If you didn't request a new password, please ignore this message and
consider reporting the incident to {self._from_address}.
""",
        )

    def send_project_request_notification(self, uuid: str):
        """Notify aministrator of a new project submission.

        :param uuid: Project temporary identifier
        :type uuid: str
        """
        self._send(
            to_address=self._notification_address,
            subject="Sci-ModoM - New project request received",
            text=f"""Project: {uuid}""",
        )


@cache
def get_mail_service() -> MailService:
    """
    Helper function to create a MailService by validating and injecting the configuration.

    :returns: Mail service instance
    :rtype: MailService
    """
    config = get_config()
    return MailService(
        url_service=get_url_service(),
        smtp_server=config.SMTP_SERVER,
        from_address=config.SMTP_FROM_ADDRESS,
        notification_address=config.NOTIFICATION_ADDRESS,
    )
