from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, String, Text
from sqlmodel import Field, SQLModel


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    # Identificador único de la categoría usando UUID nativo de PostgreSQL
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(sa.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
    )

    # Información principal de la categoría
    name: str = Field(
        sa_column=Column(String(100), nullable=False, index=True),
    )
    slug: str = Field(
        sa_column=Column(String(120), nullable=False, unique=True, index=True),
    )
    description: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Estado público de la categoría
    is_active: bool = Field(default=True, nullable=False, index=True)

    # Soft delete
    is_deleted: bool = Field(default=False, nullable=False, index=True)
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Auditoría
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
