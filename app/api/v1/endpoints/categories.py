from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_audit_log_service,
    get_category_service,
    get_current_superuser,
    get_request_id,
)
from app.schemas.auth import CurrentUser
from app.schemas.category import (
    Category as CategorySchema,
)
from app.schemas.category import (
    CategoryBasic,
    CategoryCreateRequest,
    CategoryDeleteResult,
    CategoryPartialUpdateRequest,
    CategoryRestoreResult,
    CategoryToggleStatusResult,
    CategoryUpdateRequest,
)
from app.schemas.response import ApiResponse, PagedResponse
from app.services.audit_log_service import AuditLogService
from app.services.category_service import CategoryService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[PagedResponse[CategorySchema]],
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las categorías",
    description="Devuelve una lista paginada de categorías activas y no eliminadas.",
)
async def list_categories(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: str | None = Query(None, description="Buscar por nombre, slug o descripción"),
    sort_by: str = Query("created_at", description="Campo por el cual ordenar"),
    order: str = Query("desc", description="Dirección del ordenamiento"),
    service: CategoryService = Depends(get_category_service),
):
    result = await service.get_multi_categories(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        search=search,
        is_active=True,
        is_deleted=False,
    )

    paged_data = PagedResponse[CategorySchema](
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        data=result["items"],
    )

    return ApiResponse[PagedResponse[CategorySchema]](
        codigo=200,
        mensaje="Categorías obtenidas exitosamente.",
        resultado=paged_data,
    )


@router.get(
    "/{category_id}",
    response_model=ApiResponse[CategorySchema],
    status_code=status.HTTP_200_OK,
    summary="Obtener categoría por ID",
    description="Devuelve la información detallada de una categoría activa por su ID.",
)
async def get_category_by_id(
    category_id: UUID = Path(..., description="ID de la categoría a obtener"),
    db: AsyncSession = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
):
    category = await service.get_public_category_by_id(db, category_id=category_id)

    return ApiResponse[CategorySchema](
        codigo=200,
        mensaje="Categoría obtenida exitosamente.",
        resultado=category,
    )


@router.post(
    "",
    response_model=ApiResponse[CategoryBasic],
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva categoría",
    description="Crea una nueva categoría. Requiere privilegios de superusuario.",
)
async def create_category(
    db: AsyncSession = Depends(get_db),
    category_data: CategoryCreateRequest = Body(..., description="Datos de la nueva categoría"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    new_category = await service.create_category(db, obj_in=category_data)

    await audit_log_service.log_event(
        db,
        action="create_category",
        entity="category",
        entity_id=str(new_category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Categoría creada: {new_category.name}",
    )

    return ApiResponse[CategoryBasic](
        codigo=201,
        mensaje="Categoría creada exitosamente.",
        resultado=CategoryBasic.model_validate(new_category),
    )


@router.put(
    "/{category_id}",
    response_model=ApiResponse[CategoryBasic],
    status_code=status.HTTP_200_OK,
    summary="Actualizar categoría por ID (completo)",
    description="Actualiza toda la información de una categoría. Requiere superusuario.",
)
async def update_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a actualizar"),
    category_data: CategoryUpdateRequest = Body(..., description="Datos completos de la categoría"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    updated_category = await service.update_category(
        db,
        category_id=category_id,
        obj_in=category_data,
    )

    await audit_log_service.log_event(
        db,
        action="update_category",
        entity="category",
        entity_id=str(updated_category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Actualización completa de la categoría {updated_category.name}",
    )

    return ApiResponse[CategoryBasic](
        codigo=200,
        mensaje="Categoría actualizada exitosamente.",
        resultado=CategoryBasic.model_validate(updated_category),
    )


@router.patch(
    "/{category_id}",
    response_model=ApiResponse[CategoryBasic],
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente categoría por ID",
    description="Actualiza solo los campos enviados de la categoría. Requiere superusuario.",
)
async def partial_update_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a actualizar parcialmente"),
    category_data: CategoryPartialUpdateRequest = Body(
        ..., description="Datos parciales de la categoría"
    ),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    updated_category = await service.update_category(
        db,
        category_id=category_id,
        obj_in=category_data,
    )

    await audit_log_service.log_event(
        db,
        action="partial_update_category",
        entity="category",
        entity_id=str(updated_category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Actualización parcial de la categoría {updated_category.name}",
    )

    return ApiResponse[CategoryBasic](
        codigo=200,
        mensaje="Categoría actualizada parcialmente exitosamente.",
        resultado=CategoryBasic.model_validate(updated_category),
    )


@router.patch(
    "/{category_id}/activate",
    response_model=ApiResponse[CategoryToggleStatusResult],
    status_code=status.HTTP_200_OK,
    summary="Activar una categoría",
    description="Activa una categoría que se encontraba inactiva. Requiere superusuario.",
)
async def activate_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a activar"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    category = await service.activate_category(db, category_id=category_id)

    await audit_log_service.log_event(
        db,
        action="activate_category",
        entity="category",
        entity_id=str(category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Categoría activada: {category.name}",
    )

    return ApiResponse[CategoryToggleStatusResult](
        codigo=200,
        mensaje="Categoría activada exitosamente.",
        resultado=CategoryToggleStatusResult.model_validate(category),
    )


@router.patch(
    "/{category_id}/deactivate",
    response_model=ApiResponse[CategoryToggleStatusResult],
    status_code=status.HTTP_200_OK,
    summary="Desactivar una categoría",
    description="Desactiva una categoría sin eliminarla del sistema. Requiere superusuario.",
)
async def deactivate_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a desactivar"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    category = await service.deactivate_category(db, category_id=category_id)

    await audit_log_service.log_event(
        db,
        action="deactivate_category",
        entity="category",
        entity_id=str(category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Categoría desactivada: {category.name}",
    )

    return ApiResponse[CategoryToggleStatusResult](
        codigo=200,
        mensaje="Categoría desactivada exitosamente.",
        resultado=CategoryToggleStatusResult.model_validate(category),
    )


@router.delete(
    "/{category_id}",
    response_model=ApiResponse[CategoryDeleteResult],
    status_code=status.HTTP_200_OK,
    summary="Eliminar categoría por ID",
    description="Realiza borrado lógico de una categoría. Requiere superusuario.",
)
async def delete_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a eliminar"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    deleted_category = await service.delete_category(db, category_id=category_id)

    await audit_log_service.log_event(
        db,
        action="delete_category",
        entity="category",
        entity_id=str(deleted_category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Categoría eliminada lógicamente: {deleted_category.name}",
    )

    return ApiResponse[CategoryDeleteResult](
        codigo=200,
        mensaje="Categoría eliminada exitosamente.",
        resultado=CategoryDeleteResult.model_validate(deleted_category),
    )


@router.patch(
    "/{category_id}/restore",
    response_model=ApiResponse[CategoryRestoreResult],
    status_code=status.HTTP_200_OK,
    summary="Restaurar categoría por ID",
    description="Restaura una categoría previamente eliminada lógicamente. Requiere superusuario.",
)
async def restore_category(
    db: AsyncSession = Depends(get_db),
    category_id: UUID = Path(..., description="ID de la categoría a restaurar"),
    service: CategoryService = Depends(get_category_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
    request_id: str | None = Depends(get_request_id),
):
    restored_category = await service.restore_category(db, category_id=category_id)

    await audit_log_service.log_event(
        db,
        action="restore_category",
        entity="category",
        entity_id=str(restored_category.id),
        actor=current_user,
        request_id=request_id,
        detail=f"Categoría restaurada: {restored_category.name}",
    )

    return ApiResponse[CategoryRestoreResult](
        codigo=200,
        mensaje="Categoría restaurada exitosamente.",
        resultado=CategoryRestoreResult.model_validate(restored_category),
    )
