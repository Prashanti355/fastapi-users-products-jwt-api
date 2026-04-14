from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: dict
    ) -> AuditLog:
        audit_log = AuditLog(**obj_in)
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        return audit_log