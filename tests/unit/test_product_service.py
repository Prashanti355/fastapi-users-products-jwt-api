from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions.product_exceptions import (
    InvalidProductPriceException,
    ProductAlreadyActiveException,
    ProductAlreadyDeletedException,
    ProductAlreadyExistsException,
    ProductAlreadyInactiveException,
    ProductNotDeletedException,
    ProductNotFoundException,
)
from app.models.product import Product
from app.services.product_service import ProductService


class FakeSchema:
    def __init__(self, **data):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self, exclude_unset: bool = False):
        return self._data.copy()


def build_product(
    *,
    name: str = "Laptop Lenovo",
    product_type: str = "Laptop",
    price: Decimal = Decimal("15999.99"),
    status: bool = True,
    description: str = "Producto de prueba",
    product_key: str | None = "LP1001",
    image_link: str | None = "https://example.com/product.jpg",
    is_deleted: bool = False,
) -> Product:
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
    )


@pytest.fixture
def product_repository():
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_name = AsyncMock()
    repo.get_by_product_key = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.remove = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.get_multi_products = AsyncMock()
    return repo


@pytest.fixture
def product_service(product_repository):
    return ProductService(product_repository)


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.mark.asyncio
async def test_create_product_success(product_service, product_repository, db_session):
    product_repository.get_by_name.return_value = None
    product_repository.get_by_product_key.return_value = None
    product_repository.create.return_value = build_product()

    product_in = FakeSchema(
        name="Laptop Lenovo",
        type="Laptop",
        price=Decimal("15999.99"),
        status=True,
        description="Producto de prueba",
        product_key="LP1001",
        image_link="https://example.com/product.jpg",
    )

    result = await product_service.create_product(db_session, obj_in=product_in)

    assert result.name == "Laptop Lenovo"
    product_repository.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_product_raises_when_price_is_invalid(
    product_service, product_repository, db_session
):
    product_in = FakeSchema(
        name="Laptop Lenovo",
        type="Laptop",
        price=Decimal("0"),
        status=True,
        description="Producto de prueba",
        product_key="LP1001",
        image_link="https://example.com/product.jpg",
    )

    with pytest.raises(InvalidProductPriceException):
        await product_service.create_product(db_session, obj_in=product_in)


@pytest.mark.asyncio
async def test_create_product_raises_when_name_already_exists(
    product_service, product_repository, db_session
):
    product_repository.get_by_name.return_value = build_product(name="Laptop Lenovo")

    product_in = FakeSchema(
        name="Laptop Lenovo",
        type="Laptop",
        price=Decimal("15999.99"),
        status=True,
        description="Producto de prueba",
        product_key="LP1001",
        image_link="https://example.com/product.jpg",
    )

    with pytest.raises(ProductAlreadyExistsException):
        await product_service.create_product(db_session, obj_in=product_in)


@pytest.mark.asyncio
async def test_create_product_raises_when_product_key_already_exists(
    product_service, product_repository, db_session
):
    product_repository.get_by_name.return_value = None
    product_repository.get_by_product_key.return_value = build_product(product_key="LP1001")

    product_in = FakeSchema(
        name="Laptop Lenovo",
        type="Laptop",
        price=Decimal("15999.99"),
        status=True,
        description="Producto de prueba",
        product_key="LP1001",
        image_link="https://example.com/product.jpg",
    )

    with pytest.raises(ProductAlreadyExistsException):
        await product_service.create_product(db_session, obj_in=product_in)


@pytest.mark.asyncio
async def test_get_product_by_id_success(product_service, product_repository, db_session):
    product = build_product()
    product_repository.get.return_value = product

    result = await product_service.get_product_by_id(db_session, product_id=product.id)

    assert result == product


@pytest.mark.asyncio
async def test_get_product_by_id_raises_when_not_found(
    product_service, product_repository, db_session
):
    product_repository.get.return_value = None

    with pytest.raises(ProductNotFoundException):
        await product_service.get_product_by_id(db_session, product_id=uuid4())


@pytest.mark.asyncio
async def test_get_product_by_id_raises_when_deleted_and_include_deleted_is_false(
    product_service, product_repository, db_session
):
    product = build_product(is_deleted=True)
    product_repository.get.return_value = product

    with pytest.raises(ProductNotFoundException):
        await product_service.get_product_by_id(
            db_session, product_id=product.id, include_deleted=False
        )


@pytest.mark.asyncio
async def test_get_multi_products_success(product_service, product_repository, db_session):
    product_repository.get_multi_products.return_value = {
        "total": 1,
        "page": 1,
        "limit": 10,
        "items": [build_product()],
    }

    result = await product_service.get_multi_products(db_session)

    assert result["total"] == 1
    assert len(result["items"]) == 1


@pytest.mark.asyncio
async def test_update_product_success(product_service, product_repository, db_session):
    product = build_product()
    product_repository.get.return_value = product
    product_repository.get_by_name.return_value = None
    product_repository.get_by_product_key.return_value = None
    product_repository.update.return_value = product

    product_in = FakeSchema(
        name="Laptop Lenovo Actualizada",
        type="Laptop",
        price=Decimal("14999.99"),
        status=True,
        description="Producto actualizado",
        product_key="LP1001",
        image_link="https://example.com/product-actualizado.jpg",
    )

    await product_service.update_product(db_session, product_id=product.id, obj_in=product_in)

    product_repository.update.assert_awaited_once()
    update_payload = product_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["name"] == "Laptop Lenovo Actualizada"
    assert update_payload["price"] == Decimal("14999.99")


@pytest.mark.asyncio
async def test_update_product_raises_when_price_is_invalid(
    product_service, product_repository, db_session
):
    product = build_product()
    product_repository.get.return_value = product

    product_in = FakeSchema(price=Decimal("0"))

    with pytest.raises(InvalidProductPriceException):
        await product_service.update_product(db_session, product_id=product.id, obj_in=product_in)


@pytest.mark.asyncio
async def test_update_product_raises_when_name_already_exists(
    product_service, product_repository, db_session
):
    product = build_product(name="Laptop Lenovo")
    product_repository.get.return_value = product
    product_repository.get_by_name.return_value = build_product(name="Otro Producto")

    product_in = FakeSchema(name="Laptop Lenovo Nueva", price=Decimal("14999.99"))

    with pytest.raises(ProductAlreadyExistsException):
        await product_service.update_product(db_session, product_id=product.id, obj_in=product_in)


@pytest.mark.asyncio
async def test_update_product_raises_when_product_key_already_exists(
    product_service, product_repository, db_session
):
    product = build_product(product_key="LP1001")
    product_repository.get.return_value = product
    product_repository.get_by_product_key.return_value = build_product(product_key="LP2002")

    product_in = FakeSchema(product_key="LP2002", price=Decimal("14999.99"))

    with pytest.raises(ProductAlreadyExistsException):
        await product_service.update_product(db_session, product_id=product.id, obj_in=product_in)


@pytest.mark.asyncio
async def test_delete_product_soft_delete_success(product_service, product_repository, db_session):
    product = build_product(is_deleted=False)
    product_repository.get.return_value = product
    product_repository.soft_delete.return_value = product

    await product_service.delete_product(db_session, product_id=product.id, hard_delete=False)

    product_repository.soft_delete.assert_awaited_once()
    kwargs = product_repository.soft_delete.await_args.kwargs
    assert kwargs["product_id"] == product.id


@pytest.mark.asyncio
async def test_delete_product_raises_when_already_deleted(
    product_service, product_repository, db_session
):
    product = build_product(is_deleted=True)
    product_repository.get.return_value = product

    with pytest.raises(ProductAlreadyDeletedException):
        await product_service.delete_product(db_session, product_id=product.id, hard_delete=False)


@pytest.mark.asyncio
async def test_delete_product_hard_delete_success(product_service, product_repository, db_session):
    product = build_product()
    product_repository.get.return_value = product
    product_repository.remove.return_value = product

    await product_service.delete_product(db_session, product_id=product.id, hard_delete=True)

    product_repository.remove.assert_awaited_once()


@pytest.mark.asyncio
async def test_restore_product_success(product_service, product_repository, db_session):
    product = build_product(is_deleted=True, status=False)
    product_repository.get.return_value = product
    product_repository.update.return_value = product

    await product_service.restore_product(db_session, product_id=product.id)

    product_repository.update.assert_awaited_once()
    update_payload = product_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["is_deleted"] is False
    assert update_payload["status"] is True
    assert update_payload["deleted_at"] is None


@pytest.mark.asyncio
async def test_restore_product_raises_when_product_was_not_deleted(
    product_service, product_repository, db_session
):
    product = build_product(is_deleted=False)
    product_repository.get.return_value = product

    with pytest.raises(ProductNotDeletedException):
        await product_service.restore_product(db_session, product_id=product.id)


@pytest.mark.asyncio
async def test_activate_product_success(product_service, product_repository, db_session):
    product = build_product(status=False, is_deleted=False)
    product_repository.get.return_value = product
    product_repository.update.return_value = product

    await product_service.activate_product(db_session, product_id=product.id)

    product_repository.update.assert_awaited_once()
    update_payload = product_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["status"] is True
    assert update_payload["is_deleted"] is False
    assert update_payload["deleted_at"] is None


@pytest.mark.asyncio
async def test_activate_product_raises_when_already_active(
    product_service, product_repository, db_session
):
    product = build_product(status=True, is_deleted=False)
    product_repository.get.return_value = product

    with pytest.raises(ProductAlreadyActiveException):
        await product_service.activate_product(db_session, product_id=product.id)


@pytest.mark.asyncio
async def test_deactivate_product_success(product_service, product_repository, db_session):
    product = build_product(status=True, is_deleted=False)
    product_repository.get.return_value = product
    product_repository.update.return_value = product

    await product_service.deactivate_product(db_session, product_id=product.id)

    product_repository.update.assert_awaited_once()
    update_payload = product_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["status"] is False


@pytest.mark.asyncio
async def test_deactivate_product_raises_when_already_inactive(
    product_service, product_repository, db_session
):
    product = build_product(status=False, is_deleted=False)
    product_repository.get.return_value = product

    with pytest.raises(ProductAlreadyInactiveException):
        await product_service.deactivate_product(db_session, product_id=product.id)
