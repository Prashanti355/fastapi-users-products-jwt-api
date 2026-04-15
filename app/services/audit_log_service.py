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

    async def get_audit_logs(
        self,
        db: AsyncSession,
        *,
        action: str | None = None,
        entity: str | None = None,
        actor_username: str | None = None,
        status: str | None = None,
        request_id: str | None = None,
        date_from=None,
        date_to=None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict:
        allowed_sort_fields = {
            "created_at",
            "action",
            "entity",
            "actor_username",
            "status",
        }

        if sort_by not in allowed_sort_fields:
            sort_by = "created_at"

        if order.lower() not in {"asc", "desc"}:
            order = "desc"

        return await self.repository.get_multi(
            db,
            action=action,
            entity=entity,
            actor_username=actor_username,
            status=status,
            request_id=request_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit,
            sort_by=sort_by,
            order=order,
        )