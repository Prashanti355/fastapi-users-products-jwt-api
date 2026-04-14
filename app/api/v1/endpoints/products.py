from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import (
    get_audit_log_service,
    get_current_active_user,
    get_current_superuser,
    get_product_service,
)
from app.schemas.auth import CurrentUser
from app.schemas.product import (
    Product as ProductSchema,
    ProductBasic,
    ProductCreateRequest,
    ProductDeleteResult,
    ProductPartialUpdateRequest,
    ProductRestoreResult,
    ProductToggleStatusResult,
    ProductUpdateRequest,
)
from app.schemas.response import ApiResponse, PagedResponse
from app.services.audit_log_service import AuditLogService
from app.services.product_service import ProductService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[PagedResponse[ProductSchema]],
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los productos",
    description="Devuelve una lista paginada de productos con filtros y ordenamiento."
)
async def list_products(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: Optional[str] = Query(
        None,
        description="Buscar por nombre, descripción o clave"
    ),
    status_filter: Optional[bool] = Query(
        None,
        alias="status",
        description="Filtrar por disponibilidad"
    ),
    product_type: Optional[str] = Query(
        None,
        alias="type",
        description="Filtrar por tipo de producto"
    ),
    sort_by: str = Query(
        "created_at",
        description="Campo por el cual ordenar"
    ),
    order: str = Query(
        "desc",
        description="Dirección del ordenamiento"
    ),
    service: ProductService = Depends(get_product_service),
):
    result = await service.get_multi_products(
        db,
        page=page,
        limit=limit,
        sort_by=sort_by,
        order=order,
        search=search,
        status=status_filter,
        product_type=product_type,
        is_deleted=False,
    )

    paged_data = PagedResponse[ProductSchema](
        total=result["total"],
        page=result["page"],
        limit=result["limit"],
        data=result["items"],
    )

    return ApiResponse[PagedResponse[ProductSchema]](
        codigo=200,
        mensaje="Productos obtenidos exitosamente.",
        resultado=paged_data,
    )


@router.get(
    "/{id}",
    response_model=ApiResponse[ProductSchema],
    status_code=status.HTTP_200_OK,
    summary="Obtener producto por ID",
    description="Devuelve la información detallada de un producto específico por su ID."
)
async def get_product_by_id(
    id: UUID = Path(..., description="ID del producto a obtener"),
    db: AsyncSession = Depends(get_db),
    service: ProductService = Depends(get_product_service),
):
    product = await service.get_product_by_id(
        db,
        product_id=id,
        include_deleted=False
    )

    return ApiResponse[ProductSchema](
        codigo=200,
        mensaje="Producto obtenido exitosamente.",
        resultado=product,
    )


@router.post(
    "",
    response_model=ApiResponse[ProductBasic],
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo producto",
    description="Crea un nuevo producto con la información proporcionada."
)
async def create_product(
    db: AsyncSession = Depends(get_db),
    product_data: ProductCreateRequest = Body(
        ...,
        description="Datos del nuevo producto"
    ),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    new_product = await service.create_product(
        db,
        obj_in=product_data
    )

    await audit_log_service.log_event(
        db,
        action="create_product",
        entity="product",
        entity_id=str(new_product.id),
        actor=current_user,
        detail=f"Producto creado: {new_product.name}",
    )

    return ApiResponse[ProductBasic](
        codigo=201,
        mensaje="Producto creado exitosamente.",
        resultado=ProductBasic.model_validate(new_product),
    )


@router.put(
    "/{id}",
    response_model=ApiResponse[ProductBasic],
    status_code=status.HTTP_200_OK,
    summary="Actualizar producto por ID (completo)",
    description="Actualiza toda la información de un producto específico."
)
async def update_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(..., description="ID del producto a actualizar"),
    product_data: ProductUpdateRequest = Body(
        ...,
        description="Datos completos del producto"
    ),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    updated_product = await service.update_product(
        db,
        product_id=id,
        obj_in=product_data
    )

    await audit_log_service.log_event(
        db,
        action="update_product",
        entity="product",
        entity_id=str(updated_product.id),
        actor=current_user,
        detail=f"Actualización completa del producto {updated_product.name}",
    )

    return ApiResponse[ProductBasic](
        codigo=200,
        mensaje="Producto actualizado exitosamente.",
        resultado=ProductBasic.model_validate(updated_product),
    )


@router.patch(
    "/{id}",
    response_model=ApiResponse[ProductBasic],
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente producto por ID",
    description="Actualiza solo los campos enviados del producto."
)
async def partial_update_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(
        ...,
        description="ID del producto a actualizar parcialmente"
    ),
    product_data: ProductPartialUpdateRequest = Body(
        ...,
        description="Datos parciales del producto"
    ),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    updated_product = await service.update_product(
        db,
        product_id=id,
        obj_in=product_data
    )

    await audit_log_service.log_event(
        db,
        action="partial_update_product",
        entity="product",
        entity_id=str(updated_product.id),
        actor=current_user,
        detail=f"Actualización parcial del producto {updated_product.name}",
    )

    return ApiResponse[ProductBasic](
        codigo=200,
        mensaje="Producto actualizado parcialmente exitosamente.",
        resultado=ProductBasic.model_validate(updated_product),
    )


@router.patch(
    "/{id}/activate",
    response_model=ApiResponse[ProductToggleStatusResult],
    status_code=status.HTTP_200_OK,
    summary="Activar un producto",
    description="Activa un producto que se encontraba no disponible."
)
async def activate_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(..., description="ID del producto a activar"),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    product = await service.activate_product(db, product_id=id)

    await audit_log_service.log_event(
        db,
        action="activate_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        detail=f"Producto activado: {product.name}",
    )

    return ApiResponse[ProductToggleStatusResult](
        codigo=200,
        mensaje="Producto activado exitosamente.",
        resultado=ProductToggleStatusResult.model_validate(product),
    )


@router.patch(
    "/{id}/deactivate",
    response_model=ApiResponse[ProductToggleStatusResult],
    status_code=status.HTTP_200_OK,
    summary="Desactivar un producto",
    description="Desactiva un producto sin eliminarlo del sistema."
)
async def deactivate_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(..., description="ID del producto a desactivar"),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    product = await service.deactivate_product(db, product_id=id)

    await audit_log_service.log_event(
        db,
        action="deactivate_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        detail=f"Producto desactivado: {product.name}",
    )

    return ApiResponse[ProductToggleStatusResult](
        codigo=200,
        mensaje="Producto desactivado exitosamente.",
        resultado=ProductToggleStatusResult.model_validate(product),
    )


@router.delete(
    "/{id}",
    response_model=ApiResponse[ProductDeleteResult],
    status_code=status.HTTP_200_OK,
    summary="Eliminar producto por ID",
    description="Realiza borrado lógico por defecto o físico si hard=true."
)
async def delete_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(..., description="ID del producto a eliminar"),
    hard: bool = Query(
        False,
        description="Si es true, realiza eliminación física"
    ),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    deleted_product = await service.delete_product(
        db,
        product_id=id,
        hard_delete=hard
    )

    delete_mode = "físicamente" if hard else "lógicamente"

    await audit_log_service.log_event(
        db,
        action="delete_product",
        entity="product",
        entity_id=str(deleted_product.id),
        actor=current_user,
        detail=f"Producto eliminado {delete_mode}: {deleted_product.name}",
    )

    return ApiResponse[ProductDeleteResult](
        codigo=200,
        mensaje="Producto eliminado exitosamente.",
        resultado=ProductDeleteResult.model_validate(deleted_product),
    )


@router.patch(
    "/{id}/restore",
    response_model=ApiResponse[ProductRestoreResult],
    status_code=status.HTTP_200_OK,
    summary="Restaurar producto por ID",
    description="Restaura un producto previamente eliminado lógicamente."
)
async def restore_product(
    db: AsyncSession = Depends(get_db),
    id: UUID = Path(..., description="ID del producto a restaurar"),
    service: ProductService = Depends(get_product_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
    current_user: CurrentUser = Depends(get_current_superuser),
):
    restored_product = await service.restore_product(
        db,
        product_id=id
    )

    await audit_log_service.log_event(
        db,
        action="restore_product",
        entity="product",
        entity_id=str(restored_product.id),
        actor=current_user,
        detail=f"Producto restaurado: {restored_product.name}",
    )

    return ApiResponse[ProductRestoreResult](
        codigo=200,
        mensaje="Producto restaurado exitosamente.",
        resultado=ProductRestoreResult.model_validate(restored_product),
    )