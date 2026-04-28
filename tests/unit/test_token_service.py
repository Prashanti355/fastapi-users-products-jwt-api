from uuid import uuid4

import pytest

from app.core.exceptions.auth_exceptions import (
    InvalidTokenException,
    TokenRefreshException,
)
from app.models.user import User
from app.services.token_service import TokenService


def build_test_user(
    *,
    username: str = "maya",
    email: str = "maya@example.com",
    is_superuser: bool = False,
    role: str = "user",
) -> User:
    return User(
        id=uuid4(),
        username=username,
        email=email,
        password="hashed_password_fake",
        first_name="Maya",
        last_name="Pena",
        is_active=True,
        is_superuser=is_superuser,
        is_deleted=False,
        email_verified=False,
        role=role,
    )


def test_generate_tokens_returns_access_and_refresh_token():
    user = build_test_user()

    tokens = TokenService.generate_tokens(user)

    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "bearer"
    assert tokens.expires_in > 0


def test_generate_tokens_access_token_is_valid_access_token():
    user = build_test_user(username="user_access")

    tokens = TokenService.generate_tokens(user)
    token_data = TokenService.verify_access_token(tokens.access_token)

    assert token_data.sub == str(user.id)
    assert token_data.username == user.username
    assert token_data.role == user.role
    assert token_data.is_superuser == user.is_superuser
    assert token_data.token_type == "access"


def test_generate_tokens_refresh_token_is_valid_refresh_token():
    user = build_test_user(username="admin_refresh", is_superuser=True, role="admin")

    tokens = TokenService.generate_tokens(user)
    token_data = TokenService.verify_refresh_token(tokens.refresh_token)

    assert token_data.sub == str(user.id)
    assert token_data.username == user.username
    assert token_data.role == user.role
    assert token_data.is_superuser == user.is_superuser
    assert token_data.token_type == "refresh"


def test_verify_access_token_raises_exception_when_receiving_refresh_token():
    user = build_test_user()

    tokens = TokenService.generate_tokens(user)

    with pytest.raises(InvalidTokenException):
        TokenService.verify_access_token(tokens.refresh_token)


def test_verify_refresh_token_raises_exception_when_receiving_access_token():
    user = build_test_user()

    tokens = TokenService.generate_tokens(user)

    with pytest.raises(TokenRefreshException):
        TokenService.verify_refresh_token(tokens.access_token)


def test_verify_access_token_raises_exception_for_invalid_token():
    invalid_token = "token.invalido.de.prueba"

    with pytest.raises(InvalidTokenException):
        TokenService.verify_access_token(invalid_token)


def test_verify_refresh_token_raises_exception_for_invalid_token():
    invalid_token = "token.invalido.de.prueba"

    with pytest.raises(TokenRefreshException):
        TokenService.verify_refresh_token(invalid_token)
