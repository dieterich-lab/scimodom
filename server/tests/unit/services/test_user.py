from collections import namedtuple
from typing import List

import pytest

from scimodom.services.user import UserService, WrongUserOrPassword, UserExists
from scimodom.database.models import User
from scimodom.utils.specs.enums import UserState

HistoryItem = namedtuple("HistoryItem", "operation email token")


class FakeMailService:
    def __init__(self):
        self.history: List[HistoryItem] = []

    def send_register_confirmation_token(self, email: str, token: str):
        self.history.append(HistoryItem("register", email, token))

    def send_password_reset_token(self, email: str, token: str):
        self.history.append(HistoryItem("reset", email, token))


@pytest.fixture
def mail_service():
    yield FakeMailService()


@pytest.fixture
def user_service(Session, mail_service):
    yield UserService(session=Session(), mail_service=mail_service)


def test_register_user(
    Session, user_service: UserService, mail_service: FakeMailService
):
    user_service.register_user(email="x@example.com", password="abc")
    assert len(mail_service.history) == 1
    assert mail_service.history[0].operation == "register"
    assert mail_service.history[0].email == "x@example.com"

    user_service.confirm_user("x@example.com", mail_service.history[0].token)
    assert user_service.check_password("x@example.com", "abc")
    with Session() as session:
        user = session.get_one(User, 1)
        assert user.email == "x@example.com"
        assert user.confirmation_token is None
        assert user.state == UserState.active

    # failed login check
    assert not user_service.check_password("x@example.com", "xyz")


def test_register_user_exists(
    Session, user_service: UserService, mail_service: FakeMailService
):
    with Session() as session, session.begin():
        session.add(User(email="x@example.com", state=UserState.active))
    with pytest.raises(UserExists) as exc:
        user_service.register_user(email="x@example.com", password="abc")
    assert str(exc.value) == "User with address 'x@example.com' already exists"


def test_confirm_user_bad_token(user_service: UserService):
    user_service.register_user(email="x@example.com", password="abc")
    with pytest.raises(WrongUserOrPassword):
        user_service.confirm_user("x@example.com", "xxx")


def test_confirm_user_no_user(user_service: UserService):
    with pytest.raises(WrongUserOrPassword):
        user_service.confirm_user("x@example.com", "xxx")


def test_password_reset_good(
    user_service: UserService, Session, mail_service: FakeMailService
):
    with Session() as session, session.begin():
        session.add(
            User(email="x@example.com", state=UserState.active, password_hash="xxx")
        )

    user_service.request_password_reset("x@example.com")
    assert len(mail_service.history) == 1
    assert mail_service.history[0].operation == "reset"
    assert mail_service.history[0].email == "x@example.com"

    user_service.do_password_reset(
        "x@example.com", mail_service.history[0].token, "xyz"
    )
    assert user_service.check_password("x@example.com", "xyz")


def test_password_reset_wrong_token(
    user_service: UserService, Session, mail_service: FakeMailService
):
    with Session() as session, session.begin():
        session.add(
            User(email="x@wxample.com", state=UserState.active, password_hash="xxx")
        )

    with pytest.raises(WrongUserOrPassword):
        user_service.do_password_reset("x@wxample.com", "xxx", "xyz")

    assert not user_service.check_password("x@example.com", "xyz")
