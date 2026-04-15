from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.auth import CurrentUser


class AuditLogService:
    def __init__(self, repository: AuditLogRepository):
        self.repository = repository

    async def log_event(
        self,
        db: AsyncSession,
        *,
        action: str,
        entity: str,
        entity_id: Optional[str] = None,
        actor: Optional[CurrentUser] = None,
        request_id: Optional[str] = None,
        status: str = "success",
        detail: Optional[str] = None,
    ):
        payload = {
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "actor_id": str(actor.id) if actor else None,
            "actor_username": actor.username if actor else None,
            "actor_role": actor.role if actor else None,
            "request_id": request_id,
            "status": status,
            "detail": detail,
        }

        return await self.repository.create(db, obj_in=payload)