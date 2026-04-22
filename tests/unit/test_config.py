import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(**overrides):
    base_data = {
        "POSTGRES_USER": "fastapi_app",
        "POSTGRES_PASSWORD": "fastapi_password",
        "POSTGRES_DB": "fastapi_db",
        "POSTGRES_HOST": "localhost",
        "SECRET_KEY": "x" * 32,
    }
    base_data.update(overrides)
    return Settings(**base_data)


def test_settings_builds_database_url_when_missing():
    settings_obj = build_settings(
        POSTGRES_USER="user1",
        POSTGRES_PASSWORD="pass1",
        POSTGRES_DB="db1",
        POSTGRES_HOST="dbhost",
        POSTGRES_PORT=5433,
        DATABASE_URL=None,
    )

    assert settings_obj.DATABASE_URL == (
        "postgresql+asyncpg://user1:pass1@dbhost:5433/db1"
    )


def test_settings_preserves_database_url_when_provided():
    custom_url = "postgresql+asyncpg://custom:custom@customhost:5432/customdb"

    settings_obj = build_settings(DATABASE_URL=custom_url)

    assert settings_obj.DATABASE_URL == custom_url


def test_validate_secret_key_accepts_minimum_length():
    settings_obj = build_settings(SECRET_KEY="a" * 32)

    assert settings_obj.SECRET_KEY == "a" * 32


def test_validate_secret_key_rejects_short_value():
    with pytest.raises(ValidationError) as exc_info:
        build_settings(SECRET_KEY="short-secret-key")

    assert "SECRET_KEY debe tener al menos 32 caracteres para ser segura" in str(exc_info.value)


def test_parse_cors_origins_accepts_json_list_string():
    settings_obj = build_settings(
        BACKEND_CORS_ORIGINS='["http://localhost:8000","http://localhost:5173"]'
    )

    assert settings_obj.BACKEND_CORS_ORIGINS == [
        "http://localhost:8000",
        "http://localhost:5173",
    ]


def test_parse_cors_origins_accepts_comma_separated_string():
    settings_obj = build_settings(
        BACKEND_CORS_ORIGINS="http://localhost:8000, http://localhost:5173"
    )

    assert settings_obj.BACKEND_CORS_ORIGINS == [
        "http://localhost:8000",
        "http://localhost:5173",
    ]


def test_parse_cors_origins_returns_empty_list_for_blank_string():
    settings_obj = build_settings(BACKEND_CORS_ORIGINS="   ")

    assert settings_obj.BACKEND_CORS_ORIGINS == []


def test_parse_cors_origins_preserves_list_input():
    cors_list = ["http://localhost:8000", "http://localhost:5173"]

    settings_obj = build_settings(BACKEND_CORS_ORIGINS=cors_list)

    assert settings_obj.BACKEND_CORS_ORIGINS == cors_list


def test_parse_rate_limit_defaults_accepts_json_list_string():
    settings_obj = build_settings(
        RATE_LIMIT_DEFAULTS='["100/minute","10/second"]'
    )

    assert settings_obj.RATE_LIMIT_DEFAULTS == [
        "100/minute",
        "10/second",
    ]


def test_parse_rate_limit_defaults_accepts_comma_separated_string():
    settings_obj = build_settings(
        RATE_LIMIT_DEFAULTS="100/minute, 10/second"
    )

    assert settings_obj.RATE_LIMIT_DEFAULTS == [
        "100/minute",
        "10/second",
    ]


def test_parse_rate_limit_defaults_returns_empty_list_for_blank_string():
    settings_obj = build_settings(RATE_LIMIT_DEFAULTS="   ")

    assert settings_obj.RATE_LIMIT_DEFAULTS == []


def test_parse_rate_limit_defaults_preserves_list_input():
    rate_limits = ["100/minute", "10/second"]

    settings_obj = build_settings(RATE_LIMIT_DEFAULTS=rate_limits)

    assert settings_obj.RATE_LIMIT_DEFAULTS == rate_limits


def test_settings_uses_default_values_for_general_fields(monkeypatch):
    env_keys = [
        "PROJECT_NAME",
        "VERSION",
        "DEBUG",
        "ENVIRONMENT",
        "API_V1_STR",
        "POSTGRES_PORT",
        "DATABASE_URL",
        "APP_PORT",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "DEFAULT_PAGE_SIZE",
        "MAX_PAGE_SIZE",
        "BACKEND_CORS_ORIGINS",
        "RATE_LIMIT_ENABLED",
        "RATE_LIMIT_STORAGE_URI",
        "RATE_LIMIT_HEADERS_ENABLED",
        "RATE_LIMIT_DEFAULTS",
        "RATE_LIMIT_LOGIN",
        "RATE_LIMIT_REGISTER",
    ]

    for key in env_keys:
        monkeypatch.delenv(key, raising=False)

    settings_obj = Settings(
        _env_file=None,
        POSTGRES_USER="fastapi_app",
        POSTGRES_PASSWORD="fastapi_password",
        POSTGRES_DB="fastapi_db",
        POSTGRES_HOST="localhost",
        SECRET_KEY="x" * 32,
    )

    assert settings_obj.PROJECT_NAME == "FastAPI Users & Products JWT API"
    assert settings_obj.VERSION == "1.0.0"
    assert settings_obj.DEBUG is False
    assert settings_obj.ENVIRONMENT == "development"
    assert settings_obj.API_V1_STR == "/api/v1"
    assert settings_obj.POSTGRES_PORT == 5432
    assert settings_obj.APP_PORT == 8000
    assert settings_obj.ALGORITHM == "HS256"
    assert settings_obj.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings_obj.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert settings_obj.DEFAULT_PAGE_SIZE == 10
    assert settings_obj.MAX_PAGE_SIZE == 100
    assert settings_obj.BACKEND_CORS_ORIGINS == []
    assert settings_obj.RATE_LIMIT_ENABLED is True
    assert settings_obj.RATE_LIMIT_STORAGE_URI == "memory://"
    assert settings_obj.RATE_LIMIT_HEADERS_ENABLED is True
    assert settings_obj.RATE_LIMIT_DEFAULTS == []
    assert settings_obj.RATE_LIMIT_LOGIN == "200/minute"
    assert settings_obj.RATE_LIMIT_REGISTER == "100/minute"