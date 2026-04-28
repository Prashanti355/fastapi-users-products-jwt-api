from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_audit_log_service, get_current_superuser
from app.schemas.audit_log import AuditLogRead
from app.schemas.auth import CurrentUser
from app.schemas.response import ApiResponse, PagedResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[PagedResponse[AuditLogRead]],
    status_code=status.HTTP_200_OK,
    summary="Obtener logs de auditoría",
    description="Devuelve una lista paginada de eventos de auditoría. Solo disponible para superusuario.",
)
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    action: str | None = Query(None),
    entity: str | None = Query(None),
    actor_username: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    request_id: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    result = await service.get_audit_logs(
        db,
        action=action,
        entity=entity,
        actor_username=actor_username,
        status=status_filter,
        request_id=request_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
    )

    paged_data = PagedResponse[AuditLogRead](
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        data=result["items"],
    )

    return ApiResponse[PagedResponse[AuditLogRead]](
        codigo=200,
        mensaje="Logs de auditoría obtenidos correctamente.",
        resultado=paged_data,
    )
