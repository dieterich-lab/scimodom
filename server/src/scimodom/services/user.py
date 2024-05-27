import logging
import random
import string
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from scimodom.database.models import User, UserState
from scimodom.services.mail import MailService, get_mail_service
from scimodom.database.database import get_session

logger = logging.getLogger(__name__)


class UserExists(Exception):
    pass


class WrongUserOrPassword(Exception):
    pass


class NoSuchUser(Exception):
    pass


class _DetailedWrongUserOrPassword(Exception):
    pass


class UserService:
    """Service to handle users. Beside checking a password on
    login it supports the workflows to register a user and
    to rest a password. All errors, which may caused by hacker
    attacks are logged in detailed but reported to the outside
    as a WrongUserOrPassword exception with a generic message.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param mail_service: Service used to send tokens for registration and
    password reset to the user
    :type mail_service: MailService
    """

    TOKEN_CHARACTERS = string.ascii_letters + string.digits

    def __init__(self, session: Session, mail_service: MailService):
        self._session = session
        self._mail_service = mail_service

    def register_user(self, email: str, password: str) -> None:
        """Create a new, inactive user in the database and send out
        a token to validate the email address. It may fail with a
        UserExists exception.

        :param email: A user is identified by the email address. There is no
        separate name.
        :type email: str
        :param password: Clear text password
        :type password: str
        """
        try:
            self.get_user_by_email(email)
            raise UserExists(f"User with address '{email}' already exists")
        except NoSuchUser:
            pass

        confirmation_token = self._get_random_token()
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password, method="pbkdf2"),
            state=UserState.wait_for_confirmation,
            confirmation_token=confirmation_token,
        )
        try:
            self._session.add(new_user)
            self._mail_service.send_register_confirmation_token(
                email, confirmation_token
            )
            self._session.commit()
        except Exception as exc:
            self._session.rollback()
            raise exc

    def get_user_by_email(self, email: str) -> User:
        """Get user.

        :param email: User name (email address).
        :type email: str
        :returns: User instance
        :rtype: User
        """
        stmt = select(User).where(User.email == email)
        users = list(self._session.scalars(stmt))
        if len(users) > 1:
            raise Exception(
                f"Internal Error: Found multiple users with same address '{email}'"
            )
        if len(users) == 0:
            raise NoSuchUser(f"No such user '{email}'")
        return users[0]

    def _get_random_token(self):
        return "".join(random.choice(self.TOKEN_CHARACTERS) for _ in range(32))

    def _send_email_with_confirmation_token(self, email, confirmation_token):
        pass

    def confirm_user(self, email: str, confirmation_token: str):
        """Activates a registered user with the token sent out before by email.
        If the user is active already just ignore it and count it as success.

        :param email: User name (email address).
        :type email: str
        :param confirmation_token: Token
        :type confirmation_token: str
        """
        try:
            try:
                user = self.get_user_by_email(email)
            except NoSuchUser:
                raise _DetailedWrongUserOrPassword(
                    f"Received confirmation for unknown user '{email}'"
                )
            if user.state == UserState.active:
                return
            if user.confirmation_token != confirmation_token:
                raise _DetailedWrongUserOrPassword(
                    f"Received bad confirmation token '{confirmation_token}' "
                    + f"for user '{email}' during registration"
                )

            user.state = UserState.active
            user.confirmation_token = None
            self._session.commit()

        except _DetailedWrongUserOrPassword as exc:
            logger.warning(f"{str(exc)}")
            raise WrongUserOrPassword("Wrong username or password!")

    def request_password_reset(self, email: str) -> None:
        """A token is generated and send out by email. Otherwise, the account stays
        unchanged, e.g. inactive or active. That is important, because otherwise an
        unauthenticated hacker may abuse the workflow to trigger a state change of
        the account. The workflow can also be used to retry registration if the
        initial email with the token was lost.

        :param email: User name (email address).
        :type email: str
        """
        user = self.get_user_by_email(email)
        user.confirmation_token = self._get_random_token()
        self._session.commit()
        self._mail_service.send_password_reset_token(email, user.confirmation_token)

    def do_password_reset(
        self, email: str, confirmation_token: str, new_password: str
    ) -> None:
        """Do a password reset with a token sent out before via email.

        :param email: User name (email address).
        :type email: str
        :param confirmation_token: Token
        :type confirmation_token: str
        :param new_password: New password
        :type new_password: str
        """
        try:
            try:
                user = self.get_user_by_email(email)
            except NoSuchUser:
                raise _DetailedWrongUserOrPassword(
                    f"Unknown user '{email}' tried to change the password"
                )
            if user.confirmation_token != confirmation_token:
                raise _DetailedWrongUserOrPassword(
                    f"Received bad confirmation token '{confirmation_token}' "
                    + f"for user '{email}' during password change."
                )
            self.change_password(email, new_password)
        except _DetailedWrongUserOrPassword as exc:
            logger.warning(f"{str(exc)}")
            raise WrongUserOrPassword("Wrong username or password!")

    def change_password(self, email: str, new_password: str):
        """Change a password for an authorized user.

        :param email: User name (email address).
        :type email: str
        :param new_password: New password
        :type new_password: str
        """
        try:
            user = self.get_user_by_email(email)
        except NoSuchUser:
            raise _DetailedWrongUserOrPassword(
                f"Unknown user '{email}' tried to change the password"
            )
        user.state = UserState.active
        user.password_hash = generate_password_hash(new_password, method="pbkdf2")
        user.confirmation_token = None
        self._session.commit()

    def check_password(self, email: str, password: str) -> bool:
        """Returns true if the password matches the stored password.
        Otherwise, false is returned - also in case of an unknown or inactive user.

        :param email: User name (email address).
        :type email: str
        :param password: Password
        :type password: str
        """
        try:
            user = self.get_user_by_email(email)
        except NoSuchUser:
            logger.warning(f"Unknown user '{email}' tried to login")
            return False
        if user.state != UserState.active:
            logger.warning(
                f"User '{email}' in unexpected status {user.state.name} tried to login"
            )
            return False
        if not check_password_hash(user.password_hash, password):
            logger.warning(f"User '{email}' failed to login")
            return False
        return True


_cached_user_service: Optional[UserService] = None


def get_user_service():
    """Helper function to set up a UserService object by injecting its dependencies.

    :returns: User service instance
    :rtype: UserService
    """
    global _cached_user_service
    if _cached_user_service is None:
        _cached_user_service = UserService(
            session=get_session(), mail_service=get_mail_service()
        )
    return _cached_user_service
