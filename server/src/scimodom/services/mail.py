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

    :smtp_server: A server willing to relay unauthenticated emails for us.
    :from_address: The email address used for the sender. It must be also acceptable
            for the SMTP server.
    """

    def __init__(self, smtp_server: str, from_address: str):
        self._smtp_server = smtp_server
        self._from_address = from_address

    def _send(self, to_address, subject: str, text: str):
        connection = SMTP(self._smtp_server)
        m = MIMEText(text, "plain")
        m["Subject"] = subject
        m["From"] = self._from_address
        try:
            connection.sendmail(self._from_address, to_address, m.as_string())
        finally:
            connection.quit()

    def send_register_confirmation_token(self, email: str, token: str):
        """Sends out a message to verify the email address during user registration."""
        link = get_user_registration_link(email, token)
        self._send(
            to_address=email,
            subject="SCI-MODOM - please confirm your email address",
            text=f"""
To whom it concerns,

you just registered an account with your email address

        {email}

on the SCI-MODOM server. To activate the account, please
visit this link:

        {link}

If you did NOT register, please don't click the link and
consider to report the incident too us.

Best regards
{self._from_address}
""",
        )

    def send_password_reset_token(self, email: str, token: str):
        """Sends out a message to allow the user to confirm a password reset."""
        link = get_password_reset_link(email, token)
        self._send(
            to_address=email,
            subject="SCI-MODOM - password reset",
            text=f"""
To whom it concerns,

you just requested to reset your password for

        {email}

on the SCI-MODOM server. To set your new password please
visit this link:

        {link}

If you did NOT request a password, please don't click the
link and consider to report the incident too us.

Best regards
{self._from_address}
""",
        )


_cached_mail_service: Optional[MailService] = None


def get_mail_service() -> MailService:
    """
    Helper function to create a MailService by validating and injecting the configuration.
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
