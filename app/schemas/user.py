import re
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


# =========================================================
# DTOs de lectura completos (alineados con la práctica)
# =========================================================


class UserBaseDetail(BaseModel):
    first_name: str = Field(..., max_length=150)
    last_name: str = Field(..., max_length=150)
    username: str = Field(..., max_length=20)
    email: Optional[EmailStr] = None
    is_active: bool = True
    is_superuser: bool = False
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
    role: Optional[str] = Field(None, max_length=24)


class UserRead(UserBaseDetail):
    # transicional: hoy tu modelo activo usa int; la práctica final migrará a UUID
    id: UUID | int
    last_login: Optional[datetime] = None
    date_joined: Optional[datetime] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(UserBaseDetail):
    password: str = Field(
        ..., min_length=8, description="Contraseña (se almacenará cifrada)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError(
                "La contraseña debe incluir al menos una letra y un número"
            )
        return v


class UserUpdateRequest(UserCreateRequest):
    pass


class UserPartialUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=8)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=150)
    last_name: Optional[str] = Field(None, max_length=150)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    profile_picture: Optional[HttpUrl] = None
    nationality: Optional[str] = None
    occupation: Optional[str] = None
    date_of_birth: Optional[date] = None
    contact_phone_number: Optional[str] = None
    gender: Optional[Gender] = None
    address: Optional[str] = None
    address_number: Optional[str] = None
    address_interior_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_zip_code: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    role: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
                raise ValueError(
                    "La contraseña debe incluir al menos una letra y un número"
                )
        return v


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La nueva contraseña debe incluir letras y números")
        return v


class PasswordResetRequest(BaseModel):
    email: EmailStr


class UserDeleteResult(BaseModel):
    id: UUID | int
    is_deleted: bool
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserRestoreResult(BaseModel):
    id: UUID | int
    is_deleted: bool
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserEmailVerifyResult(BaseModel):
    id: UUID | int
    email: EmailStr
    email_verified: bool
    email_verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserToggleActiveResult(BaseModel):
    id: UUID | int
    username: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PagedUsersResult(BaseModel):
    total: int
    page: int
    limit: int
    users: list[UserRead]


# =========================================================
# DTOs activos de compatibilidad con el código actual
# =========================================================


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    age: Optional[int] = Field(default=None, ge=0, le=120)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=20)
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(default=None, ge=0, le=120)


class UserResponse(BaseModel):
    id: UUID | int
    username: str
    email: EmailStr
    age: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    users: list[UserResponse]


class UserCreatedResponse(BaseModel):
    mensaje: str
    user: UserResponse


class UserUpdatedResponse(BaseModel):
    mensaje: str
    user: UserResponse


class UserDeletedResponse(BaseModel):
    mensaje: str


class UserNotFoundResponse(BaseModel):
    detail: str


class UserConflictResponse(BaseModel):
    detail: str
