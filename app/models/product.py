from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Numeric, Text
from sqlmodel import Field, SQLModel


class Product(SQLModel, table=True):
    __tablename__ = "products"

    # Identificador único del producto usando UUID nativo de PostgreSQL
    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(sa.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
    )

    # Información principal del producto
    name: str = Field(max_length=255, nullable=False, index=True)
    type: str = Field(max_length=10, nullable=False)
    price: Decimal = Field(sa_column=Column(Numeric(precision=8, scale=2), nullable=False))
    status: bool = Field(default=True, nullable=False)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    product_key: str | None = Field(default=None, max_length=8, nullable=True)
    image_link: str | None = Field(default=None, max_length=200, nullable=True)

    # Soft delete
    is_deleted: bool = Field(default=False, nullable=False)
    deleted_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
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
