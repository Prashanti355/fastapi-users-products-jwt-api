from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        nullable=False,
    )
    token: str = Field(
        max_length=255,
        nullable=False,
        index=True,
        sa_column_kwargs={"unique": True},
    )
    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    used_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )