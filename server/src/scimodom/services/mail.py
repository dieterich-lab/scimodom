from email.mime.text import MIMEText
from smtplib import SMTP
from urllib.parse import quote
from scimodom.config import Config


class MailService:
    """Server to handle email notifications. For now all email
    templates are hardcoded in English.

    :smtp_server: A server willing to relay unauthenticated emails for us.
    :from_address: The email address used for the sender. It must be also acceptable
            for the SMTP server.
    :public_url: The official URL of the SCI_MODEM instance. It is used to contract
            links for emails used in the registration and password reset workflows.
    """

    def __init__(self, smtp_server: str, from_address: str, public_url: str):
        self._smtp_server = smtp_server
        self._from_address = from_address
        self._public_url = public_url

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
        link = self._build_link("confirm_email", email, token)
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

Best regards
{self._from_address}
""",
        )

    def _build_link(self, operation, email, token):
        parts = [self._public_url]
        if self._public_url[-1] != "/":
            parts.append("/")
        parts.append(operation)
        parts.append("/")
        parts.append(quote(email))
        parts.append("/")
        parts.append(token)
        return "".join(parts)

    def send_password_reset_token(self, email: str, token: str):
        """Sends out a message to allow the user to confirm a password reset."""
        link = self._build_link("reset_password", email, token)
        self._send(
            to_address=email,
            subject="SCI-MODOM - password reset",
            text=f"""
To whom it concerns,

you just requested to reset your password for

        {email}

on the SCI-MODOM server. To set your new password please
bisit this link:

        {link}

Best regards
{self._from_address}
""",
        )


def get_mail_service():
    """Helper function to create a MailService by validating and injecting the configuration."""
    for required_parameter in ["SMTP_SERVER", "SMTP_FROM_ADDRESS", "PUBLIC_URL"]:
        value = getattr(Config, required_parameter)
        if value is None or value == "":
            raise Exception(
                f"Internal error: Required parameter '{required_parameter}' not set"
            )

    return MailService(
        smtp_server=Config.SMTP_SERVER,
        from_address=Config.SMTP_FROM_ADDRESS,
        public_url=Config.PUBLIC_URL,
    )
