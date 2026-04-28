from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions.auth_exceptions import InsufficientPermissionsException
from app.dependencies import (
    get_audit_log_service,
    get_current_active_user,
    get_current_superuser,
    get_request_id,
    get_user_service,
)
from app.schemas.auth import CurrentUser
from app.schemas.response import ApiResponse, ApiResponseSimple, PagedResponse
from app.schemas.user import (
    PasswordChangeRequest,
    UserCreateRequest,
    UserDeleteResult,
    UserPartialUpdateRequest,
    UserRestoreResult,
    UserToggleActiveResult,
    UserUpdateRequest,
)
from app.schemas.user import (
    UserRead as UserSchema,
)
from app.services.audit_log_service import AuditLogService
from app.services.user_service import UserService

router = APIRouter()


def _ensure_self_or_superuser(
    current_user: CurrentUser,
    target_user_id: UUID,
    action_message: str = "No tiene permisos para realizar esta acción.",
) -> None:
    if current_user.is_superuser:
        return

    if current_user.id != target_user_id:
        raise InsufficientPermissionsException(message=action_message)


@router.get(
    "",
    response_model=ApiResponse[PagedResponse[UserSchema]],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los usuarios",
    description="Devuelve una lista paginada de usuarios con filtros y ordenamiento.",
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    sort_by: str = Query("created_at", description="Campo por el cual ordenar"),
    order: str = Query("desc", description="Dirección del ordenamiento"),
    search: str | None = Query(None, description="Búsqueda general"),
    is_active: bool | None = Query(None, description="Filtrar por estado activo"),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    result = await user_service.get_multi_users(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        search=search,
        is_active=is_active,
        is_deleted=False,
    )

    return ApiResponse(
        codigo=200,
        mensaje="Usuarios obtenidos correctamente.",
        resultado=PagedResponse[UserSchema](**result),
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserSchema],
    status_code=status.HTTP_200_OK,
    summary="Obtener usuario por ID",
)
async def get_user(
    user_id: UUID = Path(..., description="ID del usuario"),
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    _ensure_self_or_superuser(current_user, user_id, "Solo puede consultar su propio usuario.")

    user = await user_service.get_user_by_id(db, user_id=user_id)

    return ApiResponse(codigo=200, mensaje="Usuario obtenido correctamente.", resultado=user)


@router.post(
    "",
    response_model=ApiResponse[UserSchema],
    status_code=status.HTTP_201_CREATED,
    summary="Crear nuevo usuario",
)
async def create_user(
    user_in: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    user = await user_service.create_user(db, user_in=user_in)

    await audit_log_service.log_event(
        db,
        action="create_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Usuario creado por superusuario: {user.username}",
    )

    return ApiResponse(codigo=201, mensaje="Usuario creado correctamente.", resultado=user)


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserSchema],
    status_code=status.HTTP_200_OK,
    summary="Actualización completa",
)
async def update_user(
    user_id: UUID,
    user_in: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
    request_id: str | None = Depends(get_request_id),
):
    _ensure_self_or_superuser(current_user, user_id, "Solo puede actualizar su propio usuario.")

    user = await user_service.update_user(
        db, user_id=user_id, user_in=user_in, current_user=current_user
    )

    await audit_log_service.log_event(
        db,
        action="update_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Actualización completa del usuario {user.username}",
    )

    return ApiResponse(codigo=200, mensaje="Usuario actualizado correctamente.", resultado=user)


@router.patch(
    "/{user_id}",
    response_model=ApiResponse[UserSchema],
    status_code=status.HTTP_200_OK,
    summary="Actualización parcial",
)
async def partial_update_user(
    user_id: UUID,
    user_in: UserPartialUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
    request_id: str | None = Depends(get_request_id),
):
    _ensure_self_or_superuser(current_user, user_id, "Solo puede actualizar su propio usuario.")

    user = await user_service.partial_update_user(
        db, user_id=user_id, user_in=user_in, current_user=current_user
    )

    await audit_log_service.log_event(
        db,
        action="partial_update_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Actualización parcial del usuario {user.username}",
    )

    return ApiResponse(codigo=200, mensaje="Usuario actualizado parcialmente.", resultado=user)


@router.post(
    "/{user_id}/change-password",
    response_model=ApiResponseSimple,
    status_code=status.HTTP_200_OK,
    summary="Cambiar contraseña",
)
async def change_password(
    user_id: UUID,
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
    request_id: str | None = Depends(get_request_id),
):
    if current_user.id != user_id:
        raise InsufficientPermissionsException(message="Solo puede cambiar su propia contraseña.")

    await user_service.change_password(db, user_id=user_id, password_data=password_data)

    await audit_log_service.log_event(
        db,
        action="change_password",
        entity="user",
        entity_id=str(user_id),
        actor=current_user,
        request_id=request_id,
        detail="Cambio de contraseña exitoso.",
    )

    return ApiResponseSimple(
        codigo=200, mensaje="Contraseña actualizada correctamente.", resultado={}
    )


@router.patch(
    "/{user_id}/activate",
    response_model=ApiResponse[UserToggleActiveResult],
    status_code=status.HTTP_200_OK,
    summary="Activar usuario",
)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    user = await user_service.activate_user(db, user_id=user_id)

    await audit_log_service.log_event(
        db,
        action="activate_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Usuario activado: {user.username}",
    )

    return ApiResponse(
        codigo=200,
        mensaje="Usuario activado correctamente.",
        resultado=UserToggleActiveResult(
            id=user.id, username=user.username, is_active=user.is_active
        ),
    )


@router.patch(
    "/{user_id}/deactivate",
    response_model=ApiResponse[UserToggleActiveResult],
    status_code=status.HTTP_200_OK,
    summary="Desactivar usuario",
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    user = await user_service.deactivate_user(db, user_id=user_id)

    await audit_log_service.log_event(
        db,
        action="deactivate_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Usuario desactivado: {user.username}",
    )

    return ApiResponse(
        codigo=200,
        mensaje="Usuario desactivado correctamente.",
        resultado=UserToggleActiveResult(
            id=user.id, username=user.username, is_active=user.is_active
        ),
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[UserDeleteResult],
    status_code=status.HTTP_200_OK,
    summary="Eliminar usuario",
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    user = await user_service.delete_user(db, user_id=user_id, deleted_by=current_user.id)

    await audit_log_service.log_event(
        db,
        action="delete_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Usuario eliminado lógicamente: {user.username}",
    )

    return ApiResponse(
        codigo=200,
        mensaje="Usuario eliminado correctamente.",
        resultado=UserDeleteResult(
            id=user.id, is_deleted=user.is_deleted, deleted_at=user.deleted_at
        ),
    )


@router.patch(
    "/{user_id}/restore",
    response_model=ApiResponse[UserRestoreResult],
    status_code=status.HTTP_200_OK,
    summary="Restaurar usuario",
)
async def restore_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    user = await user_service.restore_user(db, user_id=user_id)

    await audit_log_service.log_event(
        db,
        action="restore_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Usuario restaurado: {user.username}",
    )

    return ApiResponse(
        codigo=200,
        mensaje="Usuario restaurado correctamente.",
        resultado=UserRestoreResult(
            id=user.id, is_deleted=user.is_deleted, deleted_at=user.deleted_at
        ),
    )
