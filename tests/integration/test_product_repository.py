from uuid import uuid4

import pytest

from app.models.product import Product
from app.repositories.product_repository import ProductRepository


def build_product(
    *,
    suffix: str,
    name: str,
    product_type: str,
    description: str,
    price: float = 100.0,
    status: bool = True,
    is_deleted: bool = False,
) -> Product:
    return Product(
        id=uuid4(),
        name=name,
        type=product_type,
        price=price,
        status=status,
        description=description,
        product_key=f"PK{suffix[:6].upper()}",
        image_link="https://example.com/product.jpg",
        is_deleted=is_deleted,
    )


@pytest.mark.asyncio
async def test_product_repository_get_by_name_returns_product(db_session):
    repo = ProductRepository()
    suffix = uuid4().hex[:6]

    product = build_product(
        suffix=suffix,
        name=f"Prod_{suffix}",
        product_type=f"T{suffix[:3]}",
        description="Producto de prueba",
    )
    db_session.add(product)
    await db_session.commit()

    result = await repo.get_by_name(
        db_session,
        name=product.name,
    )

    assert result is not None
    assert result.id == product.id
    assert result.name == product.name


@pytest.mark.asyncio
async def test_product_repository_get_by_name_returns_none_when_missing(db_session):
    repo = ProductRepository()

    result = await repo.get_by_name(
        db_session,
        name="producto_inexistente",
    )

    assert result is None


@pytest.mark.asyncio
async def test_product_repository_get_by_product_key_returns_product(db_session):
    repo = ProductRepository()
    suffix = uuid4().hex[:6]

    product = build_product(
        suffix=suffix,
        name=f"ProdKey_{suffix}",
        product_type=f"K{suffix[:3]}",
        description="Producto con clave",
    )
    db_session.add(product)
    await db_session.commit()

    result = await repo.get_by_product_key(
        db_session,
        product_key=product.product_key,
    )

    assert result is not None
    assert result.id == product.id
    assert result.product_key == product.product_key


@pytest.mark.asyncio
async def test_product_repository_get_by_product_key_returns_none_when_missing(
    db_session,
):
    repo = ProductRepository()

    result = await repo.get_by_product_key(
        db_session,
        product_key="PKNOEXIS",
    )

    assert result is None


@pytest.mark.asyncio
async def test_product_repository_get_multi_products_applies_default_is_deleted_filter(
    db_session,
):
    repo = ProductRepository()
    suffix = uuid4().hex[:4]
    type_code = f"D{suffix}"

    visible_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"Visible_{suffix}",
        product_type=type_code,
        description="Producto visible",
        is_deleted=False,
    )
    deleted_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"Deleted_{suffix}",
        product_type=type_code,
        description="Producto eliminado",
        is_deleted=True,
    )

    db_session.add_all([visible_product, deleted_product])
    await db_session.commit()

    result = await repo.get_multi_products(
        db_session,
        page=1,
        limit=10,
        product_type=type_code,
    )

    returned_ids = {item.id for item in result["items"]}

    assert result["total"] == 1
    assert visible_product.id in returned_ids
    assert deleted_product.id not in returned_ids


@pytest.mark.asyncio
async def test_product_repository_get_multi_products_can_filter_deleted_records(
    db_session,
):
    repo = ProductRepository()
    suffix = uuid4().hex[:4]
    type_code = f"X{suffix}"

    visible_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"VisibleDel_{suffix}",
        product_type=type_code,
        description="Producto activo",
        is_deleted=False,
    )
    deleted_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"DeletedDel_{suffix}",
        product_type=type_code,
        description="Producto borrado",
        is_deleted=True,
    )

    db_session.add_all([visible_product, deleted_product])
    await db_session.commit()

    result = await repo.get_multi_products(
        db_session,
        page=1,
        limit=10,
        product_type=type_code,
        is_deleted=True,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].id == deleted_product.id


@pytest.mark.asyncio
async def test_product_repository_get_multi_products_applies_status_type_search_and_sort(
    db_session,
):
    repo = ProductRepository()
    suffix = uuid4().hex[:4]
    type_code = f"S{suffix}"
    search_token = f"tok_{suffix}"

    target_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"Alpha_{suffix}",
        product_type=type_code,
        description=f"Descripcion {search_token}",
        status=True,
    )
    wrong_status_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"Beta_{suffix}",
        product_type=type_code,
        description=f"Descripcion {search_token}",
        status=False,
    )
    wrong_search_product = build_product(
        suffix=uuid4().hex[:6],
        name=f"Gamma_{suffix}",
        product_type=type_code,
        description="Sin coincidencia",
        status=True,
    )

    db_session.add_all([target_product, wrong_status_product, wrong_search_product])
    await db_session.commit()

    result = await repo.get_multi_products(
        db_session,
        page=1,
        limit=10,
        sort_by="name",
        order="asc",
        search=search_token,
        status=True,
        product_type=type_code,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].id == target_product.id
    assert result["items"][0].name == target_product.name


@pytest.mark.asyncio
async def test_product_repository_get_multi_products_applies_pagination(db_session):
    repo = ProductRepository()
    suffix = uuid4().hex[:4]
    type_code = f"P{suffix}"

    product_z = build_product(
        suffix=uuid4().hex[:6],
        name="Zulu",
        product_type=type_code,
        description="Producto Zulu",
    )
    product_m = build_product(
        suffix=uuid4().hex[:6],
        name="Mike",
        product_type=type_code,
        description="Producto Mike",
    )
    product_a = build_product(
        suffix=uuid4().hex[:6],
        name="Alpha",
        product_type=type_code,
        description="Producto Alpha",
    )

    db_session.add_all([product_z, product_m, product_a])
    await db_session.commit()

    result = await repo.get_multi_products(
        db_session,
        page=2,
        limit=1,
        sort_by="name",
        order="desc",
        product_type=type_code,
    )

    assert result["total"] == 3
    assert result["page"] == 2
    assert result["limit"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].name == "Mike"


@pytest.mark.asyncio
async def test_product_repository_soft_delete_marks_product_deleted_and_applies_kwargs(
    db_session,
):
    repo = ProductRepository()
    suffix = uuid4().hex[:6]

    product = build_product(
        suffix=suffix,
        name=f"Soft_{suffix}",
        product_type=f"Q{suffix[:3]}",
        description="Producto para soft delete",
        status=True,
        is_deleted=False,
    )
    db_session.add(product)
    await db_session.commit()

    result = await repo.soft_delete(
        db_session,
        product_id=product.id,
        status=False,
    )

    assert result is not None
    assert result.id == product.id
    assert result.is_deleted is True
    assert result.deleted_at is not None
    assert result.status is False


@pytest.mark.asyncio
async def test_product_repository_soft_delete_returns_none_when_missing(db_session):
    repo = ProductRepository()

    result = await repo.soft_delete(
        db_session,
        product_id=uuid4(),
        status=False,
    )

    assert result is None
