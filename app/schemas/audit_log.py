from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    action: str
    entity: str
    entity_id: Optional[str] = None
    actor_id: Optional[str] = None
    actor_username: Optional[str] = None
    actor_role: Optional[str] = None
    request_id: Optional[str] = None
    status: str
    detail: Optional[str] = None
    created_at: datetime


class AuditLogFilterParams(BaseModel):
    action: Optional[str] = None
    entity: Optional[str] = None
    actor_username: Optional[str] = None
    status: Optional[str] = None
    request_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    sort_by: str = "created_at"
    order: str = "desc"