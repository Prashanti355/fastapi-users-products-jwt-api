import json
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Users & Products JWT API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"

    API_V1_STR: str = "/api/v1"

    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str | None = None

    APP_PORT: int = 8000

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100

    BACKEND_CORS_ORIGINS: list[str] = []

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URI: str = "memory://"
    RATE_LIMIT_HEADERS_ENABLED: bool = True
    RATE_LIMIT_DEFAULTS: list[str] = []
    RATE_LIMIT_LOGIN: str = "200/minute"
    RATE_LIMIT_REGISTER: str = "100/minute"

    LOG_DIR: str = "logs"

    RESEND_API_KEY: str | None = None
    EMAIL_FROM: str | None = None
    FRONTEND_RESET_PASSWORD_URL: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres para ser segura")
        return value

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("RATE_LIMIT_DEFAULTS", mode="before")
    @classmethod
    def parse_rate_limit_defaults(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return []
            if value.startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def build_database_url(self):
        if self.DATABASE_URL:
            return self

        required_fields = [
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            self.POSTGRES_DB,
            self.POSTGRES_HOST,
        ]

        if all(required_fields):
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
            return self

        raise ValueError(
            "Debe definir DATABASE_URL o proporcionar POSTGRES_USER, POSTGRES_PASSWORD, "
            "POSTGRES_DB y POSTGRES_HOST."
        )


settings = Settings()
