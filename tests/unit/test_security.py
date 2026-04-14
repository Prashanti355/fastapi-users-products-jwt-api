from datetime import timedelta

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)


def test_get_password_hash_returns_different_value_than_plain_password():
    password = "Clave1234"

    hashed_password = get_password_hash(password)

    assert hashed_password != password
    assert isinstance(hashed_password, str)
    assert len(hashed_password) > 0


def test_verify_password_returns_true_for_correct_password():
    password = "Clave1234"
    hashed_password = get_password_hash(password)

    result = verify_password(password, hashed_password)

    assert result is True


def test_verify_password_returns_false_for_incorrect_password():
    password = "Clave1234"
    hashed_password = get_password_hash(password)

    result = verify_password("OtraClave999", hashed_password)

    assert result is False


def test_create_access_token_and_verify_token_successfully():
    data = {
        "sub": "123",
        "username": "maya",
        "role": "user",
        "is_superuser": False,
    }

    token = create_access_token(data=data)
    token_data = verify_token(token, expected_type="access")

    assert token_data is not None
    assert token_data.sub == "123"
    assert token_data.username == "maya"
    assert token_data.role == "user"
    assert token_data.is_superuser is False
    assert token_data.token_type == "access"


def test_create_refresh_token_and_verify_token_successfully():
    data = {
        "sub": "456",
        "username": "admin",
        "role": "admin",
        "is_superuser": True,
    }

    token = create_refresh_token(data=data)
    token_data = verify_token(token, expected_type="refresh")

    assert token_data is not None
    assert token_data.sub == "456"
    assert token_data.username == "admin"
    assert token_data.role == "admin"
    assert token_data.is_superuser is True
    assert token_data.token_type == "refresh"


def test_verify_token_returns_none_when_token_type_is_incorrect():
    data = {
        "sub": "789",
        "username": "producto",
        "role": "user",
        "is_superuser": False,
    }

    refresh_token = create_refresh_token(data=data)
    token_data = verify_token(refresh_token, expected_type="access")

    assert token_data is None


def test_verify_token_returns_none_for_invalid_token():
    invalid_token = "esto.no.es.un.jwt.valido"

    token_data = verify_token(invalid_token, expected_type="access")

    assert token_data is None


def test_verify_token_returns_none_for_expired_access_token():
    data = {
        "sub": "100",
        "username": "expirado",
        "role": "user",
        "is_superuser": False,
    }

    expired_token = create_access_token(
        data=data,
        expires_delta=timedelta(seconds=-1)
    )

    token_data = verify_token(expired_token, expected_type="access")

    assert token_data is None


def test_verify_token_returns_none_when_sub_is_missing():
    data = {
        "username": "sin_sub",
        "role": "user",
        "is_superuser": False,
    }

    token = create_access_token(data=data)
    token_data = verify_token(token, expected_type="access")

    assert token_data is None