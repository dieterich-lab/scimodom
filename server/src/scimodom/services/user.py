import logging
import random
import string

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from scimodom.database.models import User, UserState
from scimodom.services.mail import MailService

logger = logging.getLogger(__name__)


class UserExists(Exception):
    pass


class WrongUserOrPassword(Exception):
    pass


class NoSuchUser(Exception):
    pass


class DetailedWrongUserOrPassword(Exception):
    pass


class UserService:
    TOKEN_CHARACTERS = string.ascii_letters + string.digits

    def __init__(self, session: Session, mail_service: MailService):
        self._session = session
        self._mail_service = mail_service

    def register_user(self, email: str, password: str) -> None:
        try:
            self._get_user_by_email(email)
            raise UserExists(f"User with email address '{email} exists already")
        except NoSuchUser:
            pass

        confirmation_token = self._get_random_token()
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password, method="pbkdf2"),
            state=UserState.wait_for_confirmation,
            confirmation_token=confirmation_token,
        )
        self._session.add(new_user)
        self._session.commit()
        self._mail_service.send_register_confirmation_token(email, confirmation_token)

    def _get_user_by_email(self, email) -> User:
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
        try:
            try:
                user = self._get_user_by_email(email)
            except NoSuchUser:
                raise DetailedWrongUserOrPassword(
                    f"Received confirmation for unknown user '{email}'"
                )
            if user.state != UserState.wait_for_confirmation:
                raise DetailedWrongUserOrPassword(
                    f"Received confirmation for user '{email}' in unexpected status {user.state.value}"
                )
            if user.confirmation_token != confirmation_token:
                raise DetailedWrongUserOrPassword(
                    f"Received bad confirmation token '{confirmation_token}'"
                    + f"for user '{email} during registration'."
                )

            user.state = UserState.active
            user.confirmation_token = None
            self._session.commit()

        except DetailedWrongUserOrPassword as e:
            logger.warning(f"WARNING: {str(e)}")
            raise WrongUserOrPassword("Go away hacker!")

    def request_password_reset(self, email: str) -> None:
        user = self._get_user_by_email(email)
        user.confirmation_token = self._get_random_token()
        user.state = UserState.password_reset_requested
        self._session.commit()
        self._mail_service.send_password_reset_token(email, user.confirmation_token)

    def do_password_reset(self, email, confirmation_token, new_password) -> None:
        try:
            try:
                user = self._get_user_by_email(email)
            except NoSuchUser:
                raise DetailedWrongUserOrPassword(
                    f"Unknown user '{email}' tried to change the password"
                )
            if user.state != UserState.password_reset_requested:
                raise DetailedWrongUserOrPassword(
                    f"User '{email}' in unexpected status {user.state.value} tried to change the password"
                )
            if user.confirmation_token != confirmation_token:
                raise DetailedWrongUserOrPassword(
                    f"Received bad confirmation token '{confirmation_token}' "
                    + f"for user '{email}' during password change."
                )

            user.state = UserState.active
            user.password_hash = generate_password_hash(new_password, method="pbkdf2")
            user.confirmation_token = None
            self._session.commit()

        except DetailedWrongUserOrPassword as e:
            logger.warning(f"WARNING: {str(e)}")
            raise WrongUserOrPassword("Go away hacker!")

    def check_password(self, email, password) -> bool:
        try:
            user = self._get_user_by_email(email)
        except NoSuchUser:
            logger.warning(f"WARNING: Unknown user '{email}' tried to login")
            return False
        if user.state != UserState.active:
            logger.warning(
                f"WARNING: User '{email}' in unexpected status {user.state.value} tried to login"
            )
            return False
        if not check_password_hash(user.password_hash, password):
            logger.warning(f"WARNING: User '{email}' failed to login")
            return False
        return True
