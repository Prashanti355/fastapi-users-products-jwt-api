from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    entity: str
    entity_id: str | None = None
    actor_id: str | None = None
    actor_username: str | None = None
    actor_role: str | None = None
    request_id: str | None = None
    status: str
    detail: str | None = None
    created_at: datetime


class AuditLogFilterParams(BaseModel):
    action: str | None = None
    entity: str | None = None
    actor_username: str | None = None
    status: str | None = None
    request_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: str = "created_at"
    order: str = "desc"
