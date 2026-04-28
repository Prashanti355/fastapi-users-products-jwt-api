from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator

from app.schemas.user import Gender


class LoginRequest(BaseModel):
    """
    DTO para la solicitud de inicio de sesión.
    """

    username: str = Field(..., max_length=20, description="Nombre de usuario")
    password: str = Field(..., min_length=8, description="Contraseña del usuario")


class PublicRegisterRequest(BaseModel):
    """
    DTO público para registro.
    Solo incluye campos que un usuario normal puede enviar.
    """

    first_name: str = Field(..., max_length=150)
    last_name: str = Field(..., max_length=150)
    username: str = Field(..., max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)

    profile_picture: Optional[HttpUrl] = None
    nationality: Optional[str] = Field(None, max_length=7)
    occupation: Optional[str] = Field(None, max_length=17)
    date_of_birth: Optional[date] = None
    contact_phone_number: Optional[str] = Field(None, max_length=20)
    gender: Optional[Gender] = None

    address: Optional[str] = None
    address_number: Optional[str] = Field(None, max_length=25)
    address_interior_number: Optional[str] = Field(None, max_length=26)
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_zip_code: Optional[str] = Field(None, max_length=10)
    address_city: Optional[str] = Field(None, max_length=100)
    address_state: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        has_letter = any(ch.isalpha() for ch in v)
        has_digit = any(ch.isdigit() for ch in v)

        if not (has_letter and has_digit):
            raise ValueError(
                "La contraseña debe incluir al menos una letra y un número."
            )
        return v


class TokenResponse(BaseModel):
    """
    DTO de respuesta con los tokens generados.
    """

    access_token: str = Field(..., description="Token JWT de acceso")
    refresh_token: str = Field(..., description="Token JWT de refresco")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(
        ..., description="Tiempo de expiración del access token en segundos"
    )


class RefreshTokenRequest(BaseModel):
    """
    DTO para solicitar un nuevo par de tokens
    usando el refresh token.
    """

    refresh_token: str = Field(..., description="Token de refresco válido")


class TokenData(BaseModel):
    """
    Datos decodificados del token JWT (claims internos).
    """

    sub: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    is_superuser: bool = False
    token_type: Optional[str] = None
    exp: Optional[int] = None
    jti: Optional[str] = None


class CurrentUser(BaseModel):
    """
    Representa al usuario autenticado extraído del token JWT
    y validado contra la base de datos.
    """

    id: UUID
    username: str
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20, max_length=255)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetDebugResult(BaseModel):
    email: str
    token: str
    expires_at: datetime
    used_at: datetime | None = None
