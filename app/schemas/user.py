import re
from datetime import date, datetime
from enum import Enum
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
    email: EmailStr | None = None
    is_active: bool = True
    is_superuser: bool = False
    profile_picture: HttpUrl | None = None
    nationality: str | None = Field(None, max_length=7)
    occupation: str | None = Field(None, max_length=17)
    date_of_birth: date | None = None
    contact_phone_number: str | None = Field(None, max_length=20)
    gender: Gender | None = None
    address: str | None = None
    address_number: str | None = Field(None, max_length=25)
    address_interior_number: str | None = Field(None, max_length=26)
    address_complement: str | None = None
    address_neighborhood: str | None = None
    address_zip_code: str | None = Field(None, max_length=10)
    address_city: str | None = Field(None, max_length=100)
    address_state: str | None = Field(None, max_length=100)
    role: str | None = Field(None, max_length=24)


class UserRead(UserBaseDetail):
    # transicional: hoy tu modelo activo usa int; la práctica final migrará a UUID
    id: UUID | int
    last_login: datetime | None = None
    date_joined: datetime | None = None
    created_at: datetime | None = None
    modified_at: datetime | None = None
    is_deleted: bool = False
    deleted_at: datetime | None = None
    email_verified: bool = False
    email_verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(UserBaseDetail):
    password: str = Field(..., min_length=8, description="Contraseña (se almacenará cifrada)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("La contraseña debe incluir al menos una letra y un número")
        return v


class UserUpdateRequest(UserCreateRequest):
    pass


class UserPartialUpdateRequest(BaseModel):
    username: str | None = Field(None, max_length=20)
    password: str | None = Field(None, min_length=8)
    email: EmailStr | None = None
    first_name: str | None = Field(None, max_length=150)
    last_name: str | None = Field(None, max_length=150)
    is_active: bool | None = None
    is_superuser: bool | None = None
    profile_picture: HttpUrl | None = None
    nationality: str | None = None
    occupation: str | None = None
    date_of_birth: date | None = None
    contact_phone_number: str | None = None
    gender: Gender | None = None
    address: str | None = None
    address_number: str | None = None
    address_interior_number: str | None = None
    address_complement: str | None = None
    address_neighborhood: str | None = None
    address_zip_code: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    role: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None:
            if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
                raise ValueError("La contraseña debe incluir al menos una letra y un número")
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
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRestoreResult(BaseModel):
    id: UUID | int
    is_deleted: bool
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserEmailVerifyResult(BaseModel):
    id: UUID | int
    email: EmailStr
    email_verified: bool
    email_verified_at: datetime | None = None

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
    age: int | None = Field(default=None, ge=0, le=120)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=20)
    email: EmailStr | None = None
    age: int | None = Field(default=None, ge=0, le=120)


class UserResponse(BaseModel):
    id: UUID | int
    username: str
    email: EmailStr
    age: int | None = None

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
