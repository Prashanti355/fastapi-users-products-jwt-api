from __future__ import annotations

from datetime import datetime

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: dict,
    ) -> AuditLog:
        audit_log = AuditLog(**obj_in)
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        return audit_log

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        action: str | None = None,
        entity: str | None = None,
        actor_username: str | None = None,
        status: str | None = None,
        request_id: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict:
        filters = []

        if action:
            filters.append(AuditLog.action == action)

        if entity:
            filters.append(AuditLog.entity == entity)

        if actor_username:
            filters.append(AuditLog.actor_username == actor_username)

        if status:
            filters.append(AuditLog.status == status)

        if request_id:
            filters.append(AuditLog.request_id == request_id)

        if date_from:
            filters.append(AuditLog.created_at >= date_from)

        if date_to:
            filters.append(AuditLog.created_at <= date_to)

        sortable_fields = {
            "created_at": AuditLog.created_at,
            "action": AuditLog.action,
            "entity": AuditLog.entity,
            "actor_username": AuditLog.actor_username,
            "status": AuditLog.status,
        }

        sort_column = sortable_fields.get(sort_by, AuditLog.created_at)
        sort_expression = (
            desc(sort_column) if order.lower() == "desc" else asc(sort_column)
        )

        total_stmt = select(func.count()).select_from(AuditLog)
        items_stmt = select(AuditLog)

        if filters:
            total_stmt = total_stmt.where(*filters)
            items_stmt = items_stmt.where(*filters)

        total_result = await db.execute(total_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * limit

        items_stmt = items_stmt.order_by(sort_expression).offset(offset).limit(limit)

        items_result = await db.execute(items_stmt)
        items = items_result.scalars().all()

        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": items,
        }
