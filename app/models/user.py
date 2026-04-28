from datetime import date, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(sa.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
    )

    # Autenticación y seguridad
    username: str = Field(max_length=20, unique=True, nullable=False, index=True)
    email: str | None = Field(default=None, max_length=254, unique=True, nullable=True, index=True)
    password: str = Field(max_length=128, nullable=False)

    # Estado del usuario
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    is_deleted: bool = Field(default=False, nullable=False)

    # Información personal
    first_name: str = Field(max_length=150, nullable=False)
    last_name: str = Field(max_length=150, nullable=False)
    gender: str | None = Field(default=None, max_length=6, nullable=True)
    nationality: str | None = Field(default=None, max_length=7, nullable=True)
    occupation: str | None = Field(default=None, max_length=17, nullable=True)
    date_of_birth: date | None = Field(default=None, sa_column=Column(sa.Date, nullable=True))
    contact_phone_number: str | None = Field(default=None, max_length=20, nullable=True)
    profile_picture: str | None = Field(default=None, max_length=100, nullable=True)
    role: str | None = Field(default=None, max_length=24, nullable=True)

    # Verificación de email
    email_verified: bool = Field(default=False, nullable=False)
    email_verified_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    # Dirección
    address: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    address_number: str | None = Field(default=None, max_length=25, nullable=True)
    address_interior_number: str | None = Field(default=None, max_length=26, nullable=True)
    address_complement: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    address_neighborhood: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    address_zip_code: str | None = Field(default=None, max_length=10, nullable=True)
    address_city: str | None = Field(default=None, max_length=100, nullable=True)
    address_state: str | None = Field(default=None, max_length=100, nullable=True)

    # Auditoría y tiempos
    last_login: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    date_joined: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    )
    modified_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        )
    )
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    deleted_by: UUID | None = Field(
        default=None, sa_column=Column(sa.UUID(as_uuid=True), nullable=True)
    )
    deactivation_reason: str | None = Field(
        default=None, sa_column=Column(sa.String(length=255), nullable=True)
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_authenticated(self) -> bool:
        return self.is_active and not self.is_deleted

    @property
    def age(self) -> int | None:
        if not self.date_of_birth:
            return None

        today = date.today()
        age = today.year - self.date_of_birth.year

        if (today.month, today.day) < (
            self.date_of_birth.month,
            self.date_of_birth.day,
        ):
            age -= 1

        return age
