from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )

    action: str = Field(sa_column=Column(String(100), nullable=False, index=True))

    entity: str = Field(sa_column=Column(String(100), nullable=False, index=True))

    entity_id: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True, index=True)
    )

    actor_id: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True, index=True)
    )

    actor_username: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True, index=True)
    )

    actor_role: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))

    request_id: str | None = Field(
        default=None, sa_column=Column(String(100), nullable=True, index=True)
    )

    status: str = Field(default="success", sa_column=Column(String(30), nullable=False, index=True))

    detail: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
