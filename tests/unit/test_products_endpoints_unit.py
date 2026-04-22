from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
import pytest

from app.api.v1.endpoints.products import (
    activate_product,
    create_product,
    deactivate_product,
    delete_product,
    get_product_by_id,
    list_products,
    partial_update_product,
    restore_product,
    update_product,
)
from app.models.product import Product
from app.schemas.auth import CurrentUser


def build_product(
    *,
    name: str = "Laptop Pro",
    product_type: str = "Laptop",
    price: float = 14999.99,
    status: bool = True,
    description: str = "Equipo de prueba",
    product_key: str = "PK123456",
    image_link: str = "https://example.com/product.jpg",
    is_deleted: bool = False,
) -> Product:
    now_utc = datetime.now(timezone.utc)

    return Product(
        id=uuid4(),
        name=name,
        type=product_type,
        price=price,
        status=status,
        description=description,
        product_key=product_key,
        image_link=image_link,
        is_deleted=is_deleted,
        created_at=now_utc,
        modified_at=now_utc,
    )


def build_current_user(
    *,
    user_id=None,
    username: str = "maya",
    email: str = "maya@example.com",
    is_superuser: bool = False,
    is_active: bool = True,
    role: str = "user",
) -> CurrentUser:
    return CurrentUser(
        id=user_id or uuid4(),
        username=username,
        email=email,
        is_superuser=is_superuser,
        is_active=is_active,
        role=role,
    )


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.fixture
def product_service():
    service = MagicMock()
    service.get_multi_products = AsyncMock()
    service.get_product_by_id = AsyncMock()
    service.create_product = AsyncMock()
    service.update_product = AsyncMock()
    service.activate_product = AsyncMock()
    service.deactivate_product = AsyncMock()
    service.delete_product = AsyncMock()
    service.restore_product = AsyncMock()
    return service


@pytest.fixture
def audit_log_service():
    service = MagicMock()
    service.log_event = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_list_products_returns_paged_response(db_session, product_service):
    product = build_product()
    product_service.get_multi_products.return_value = {
        "total": 1,
        "page": 1,
        "limit": 10,
        "items": [product],
    }

    response = await list_products(
        db=db_session,
        page=1,
        limit=10,
        search=None,
        status_filter=None,
        product_type=None,
        sort_by="created_at",
        order="desc",
        service=product_service,
    )

    assert response.codigo == 200
    assert response.mensaje == "Productos obtenidos exitosamente."
    assert response.resultado.total == 1
    assert response.resultado.page == 1
    assert response.resultado.limit == 10
    assert len(response.resultado.data) == 1
    assert response.resultado.data[0].id == product.id
    assert response.resultado.data[0].name == product.name

    product_service.get_multi_products.assert_awaited_once_with(
        db_session,
        page=1,
        limit=10,
        sort_by="created_at",
        order="desc",
        search=None,
        status=None,
        product_type=None,
        is_deleted=False,
    )


@pytest.mark.asyncio
async def test_get_product_by_id_returns_api_response(db_session, product_service):
    product = build_product()
    product_service.get_product_by_id.return_value = product

    response = await get_product_by_id(
        id=product.id,
        db=db_session,
        service=product_service,
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto obtenido exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name

    product_service.get_product_by_id.assert_awaited_once_with(
        db_session,
        product_id=product.id,
        include_deleted=False,
    )


@pytest.mark.asyncio
async def test_create_product_logs_event_and_returns_basic_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user()
    product = build_product()
    product_data = MagicMock()

    product_service.create_product.return_value = product

    response = await create_product(
        db=db_session,
        product_data=product_data,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-create-product",
    )

    assert response.codigo == 201
    assert response.mensaje == "Producto creado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name

    product_service.create_product.assert_awaited_once_with(
        db_session,
        obj_in=product_data,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="create_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-create-product",
        detail=f"Producto creado: {product.name}",
    )


@pytest.mark.asyncio
async def test_update_product_logs_event_and_returns_basic_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user()
    product = build_product()
    product_data = MagicMock()

    product_service.update_product.return_value = product

    response = await update_product(
        db=db_session,
        id=product.id,
        product_data=product_data,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-update-product",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto actualizado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name

    product_service.update_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
        obj_in=product_data,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="update_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-update-product",
        detail=f"Actualización completa del producto {product.name}",
    )


@pytest.mark.asyncio
async def test_partial_update_product_logs_event_and_returns_basic_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user()
    product = build_product()
    product_data = MagicMock()

    product_service.update_product.return_value = product

    response = await partial_update_product(
        db=db_session,
        id=product.id,
        product_data=product_data,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-partial-update-product",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto actualizado parcialmente exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name

    product_service.update_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
        obj_in=product_data,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="partial_update_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-partial-update-product",
        detail=f"Actualización parcial del producto {product.name}",
    )


@pytest.mark.asyncio
async def test_activate_product_logs_event_and_returns_toggle_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    product = build_product(status=True)

    product_service.activate_product.return_value = product

    response = await activate_product(
        db=db_session,
        id=product.id,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-activate-product",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto activado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name
    assert response.resultado.status is True

    product_service.activate_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="activate_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-activate-product",
        detail=f"Producto activado: {product.name}",
    )


@pytest.mark.asyncio
async def test_deactivate_product_logs_event_and_returns_toggle_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    product = build_product(status=False)

    product_service.deactivate_product.return_value = product

    response = await deactivate_product(
        db=db_session,
        id=product.id,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-deactivate-product",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto desactivado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.name == product.name
    assert response.resultado.status is False

    product_service.deactivate_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="deactivate_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-deactivate-product",
        detail=f"Producto desactivado: {product.name}",
    )


@pytest.mark.asyncio
async def test_delete_product_logs_event_and_returns_delete_response_soft_delete(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    product = build_product(is_deleted=True)

    product_service.delete_product.return_value = product

    response = await delete_product(
        db=db_session,
        id=product.id,
        hard=False,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-delete-product-soft",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto eliminado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.is_deleted is True

    product_service.delete_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
        hard_delete=False,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="delete_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-delete-product-soft",
        detail=f"Producto eliminado lógicamente: {product.name}",
    )


@pytest.mark.asyncio
async def test_delete_product_logs_event_and_returns_delete_response_hard_delete(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    product = build_product(is_deleted=True)

    product_service.delete_product.return_value = product

    response = await delete_product(
        db=db_session,
        id=product.id,
        hard=True,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-delete-product-hard",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto eliminado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.is_deleted is True

    product_service.delete_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
        hard_delete=True,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="delete_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-delete-product-hard",
        detail=f"Producto eliminado físicamente: {product.name}",
    )


@pytest.mark.asyncio
async def test_restore_product_logs_event_and_returns_restore_response(
    db_session,
    product_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    product = build_product(is_deleted=False)

    product_service.restore_product.return_value = product

    response = await restore_product(
        db=db_session,
        id=product.id,
        service=product_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-restore-product",
    )

    assert response.codigo == 200
    assert response.mensaje == "Producto restaurado exitosamente."
    assert response.resultado.id == product.id
    assert response.resultado.is_deleted is False

    product_service.restore_product.assert_awaited_once_with(
        db_session,
        product_id=product.id,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="restore_product",
        entity="product",
        entity_id=str(product.id),
        actor=current_user,
        request_id="req-restore-product",
        detail=f"Producto restaurado: {product.name}",
    )