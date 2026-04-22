from datetime import date as real_date
from uuid import uuid4

from app.models.user import User


def build_user(
    *,
    username: str = "maya",
    email: str = "maya@example.com",
    password: str = "hashed_password",
    is_active: bool = True,
    is_superuser: bool = False,
    is_deleted: bool = False,
    role: str = "user",
    first_name: str = "Maya",
    last_name: str = "Pena",
    date_of_birth=None,
) -> User:
    return User(
        id=uuid4(),
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        email_verified=False,
        role=role,
        date_of_birth=date_of_birth,
    )


def test_user_full_name_returns_first_and_last_name():
    user = build_user(first_name="Maya", last_name="Guevara")

    assert user.full_name == "Maya Guevara"


def test_user_is_authenticated_returns_true_for_active_non_deleted_user():
    user = build_user(is_active=True, is_deleted=False)

    assert user.is_authenticated is True


def test_user_is_authenticated_returns_false_for_inactive_user():
    user = build_user(is_active=False, is_deleted=False)

    assert user.is_authenticated is False


def test_user_is_authenticated_returns_false_for_deleted_user():
    user = build_user(is_active=True, is_deleted=True)

    assert user.is_authenticated is False


def test_user_age_returns_none_when_date_of_birth_is_missing():
    user = build_user(date_of_birth=None)

    assert user.age is None


def test_user_age_returns_expected_value_when_birthday_already_occurred(mocker):
    class FakeDate(real_date):
        @classmethod
        def today(cls):
            return cls(2026, 4, 21)

    mocker.patch("app.models.user.date", FakeDate)

    user = build_user(date_of_birth=FakeDate(1996, 4, 20))

    assert user.age == 30


def test_user_age_returns_expected_value_when_birthday_is_today(mocker):
    class FakeDate(real_date):
        @classmethod
        def today(cls):
            return cls(2026, 4, 21)

    mocker.patch("app.models.user.date", FakeDate)

    user = build_user(date_of_birth=FakeDate(1996, 4, 21))

    assert user.age == 30


def test_user_age_returns_expected_value_when_birthday_has_not_occurred_yet(mocker):
    class FakeDate(real_date):
        @classmethod
        def today(cls):
            return cls(2026, 4, 21)

    mocker.patch("app.models.user.date", FakeDate)

    user = build_user(date_of_birth=FakeDate(1996, 4, 22))

    assert user.age == 29