from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime, String, text


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    jti: str = Field(
        sa_column=Column(String(100), unique=True, index=True, nullable=False)
    )
    user_id: UUID = Field(index=True, nullable=False)
    token_type: str = Field(
        sa_column=Column(String(20), nullable=False, default="refresh")
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    revoke_reason: Optional[str] = Field(
        default=None,
        sa_column=Column(String(100), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=text("now()"),
        ),
    )