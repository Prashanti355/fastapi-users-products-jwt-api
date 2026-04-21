from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.core.security import get_password_hash
from app.models.product import Product
from app.models.user import User
from app.repositories.base import BaseRepository


class ProductCreateSchema(BaseModel):
    name: str
    type: str
    price: float
    status: bool
    description: str
    product_key: str
    image_link: str


class ProductUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None


def build_product(
    *,
    suffix: str,
    name: str,
    product_type: str,
    description: str,
    price: float = 100.0,
    status: bool = True,
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
        is_deleted=False,
    )


def build_user(*, suffix: str) -> User:
    return User(
        id=uuid4(),
        username=f"user_{suffix}",
        email=f"user_{suffix}@example.com",
        password=get_password_hash("Clave1234"),
        first_name="Maya",
        last_name="Repository",
        is_active=True,
        is_superuser=False,
        is_deleted=False,
        email_verified=False,
        role="user",
    )


@pytest.mark.asyncio
async def test_base_repository_create_with_dict_and_get(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:8]
    short_key = suffix[:6].upper()

    created = await repo.create(
        db_session,
        obj_in={
            "name": f"Producto_{suffix}",
            "type": "Laptop",
            "price": 15999.99,
            "status": True,
            "description": f"Producto creado con dict {suffix}",
            "product_key": f"PK{short_key}",
            "image_link": "https://example.com/product.jpg",
            "is_deleted": False,
        },
    )

    fetched = await repo.get(db_session, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == f"Producto_{suffix}"
    assert fetched.product_key == f"PK{short_key}"


@pytest.mark.asyncio
async def test_base_repository_create_with_schema_and_update_with_schema(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:8]
    short_key = suffix[:6].upper()

    create_schema = ProductCreateSchema(
        name=f"ProductoSchema_{suffix}",
        type="Tablet",
        price=9999.99,
        status=True,
        description=f"Producto creado con schema {suffix}",
        product_key=f"PS{short_key}",
        image_link="https://example.com/schema.jpg",
    )

    created = await repo.create(
        db_session,
        obj_in=create_schema,
    )

    previous_modified_at = created.modified_at

    update_schema = ProductUpdateSchema(
        description="Descripción actualizada desde schema",
        price=8888.88,
    )

    updated = await repo.update(
        db_session,
        db_obj=created,
        obj_in=update_schema,
    )

    assert updated.id == created.id
    assert updated.name == create_schema.name
    assert updated.description == "Descripción actualizada desde schema"
    assert float(updated.price) == 8888.88
    assert updated.modified_at is not None
    assert previous_modified_at is not None
    assert updated.modified_at >= previous_modified_at


@pytest.mark.asyncio
async def test_base_repository_update_with_dict_ignores_unknown_fields(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:8]

    product = build_product(
        suffix=suffix,
        name=f"ProductoUpdate_{suffix}",
        product_type="Monitor",
        description="Descripción inicial",
        price=4500.00,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    previous_modified_at = product.modified_at

    updated = await repo.update(
        db_session,
        db_obj=product,
        obj_in={
            "description": "Descripción actualizada con dict",
            "price": 4999.99,
            "campo_inexistente": "ignorar",
        },
    )

    assert updated.description == "Descripción actualizada con dict"
    assert float(updated.price) == 4999.99
    assert not hasattr(updated, "campo_inexistente")
    assert updated.modified_at is not None
    assert previous_modified_at is not None
    assert updated.modified_at >= previous_modified_at


@pytest.mark.asyncio
async def test_base_repository_get_multi_applies_scalar_filters_search_and_sort(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:4]

    unique_type = f"L{suffix}"
    other_type = f"T{suffix}"
    unique_search = f"prof_{suffix}"

    product_1 = build_product(
        suffix=uuid4().hex[:8],
        name=f"Alpha_{suffix}",
        product_type=unique_type,
        description=f"Equipo {unique_search}",
        price=20000.00,
    )
    product_2 = build_product(
        suffix=uuid4().hex[:8],
        name=f"Beta_{suffix}",
        product_type=other_type,
        description=f"Equipo {unique_search}",
        price=9000.00,
    )
    product_3 = build_product(
        suffix=uuid4().hex[:8],
        name=f"Gamma_{suffix}",
        product_type=unique_type,
        description="Uso domestico",
        price=15000.00,
    )

    db_session.add_all([product_1, product_2, product_3])
    await db_session.commit()

    result = await repo.get_multi(
        db_session,
        page=1,
        limit=10,
        sort_by="name",
        order="asc",
        filters={"type": unique_type},
        search=unique_search,
        search_fields=["name", "description"],
    )

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["limit"] == 10
    assert len(result["items"]) == 1
    assert result["items"][0].id == product_1.id
    assert result["items"][0].name == product_1.name

@pytest.mark.asyncio
async def test_base_repository_get_multi_applies_list_filters_and_pagination(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:4]

    type_a = f"L{suffix}"
    type_b = f"T{suffix}"
    type_c = f"P{suffix}"

    product_1 = build_product(
        suffix=uuid4().hex[:8],
        name="Zulu Laptop",
        product_type=type_a,
        description="Producto Zulu",
    )
    product_2 = build_product(
        suffix=uuid4().hex[:8],
        name="Mike Tablet",
        product_type=type_b,
        description="Producto Mike",
    )
    product_3 = build_product(
        suffix=uuid4().hex[:8],
        name="Alpha Phone",
        product_type=type_c,
        description="Producto Alpha",
    )

    db_session.add_all([product_1, product_2, product_3])
    await db_session.commit()

    result = await repo.get_multi(
        db_session,
        page=2,
        limit=1,
        sort_by="name",
        order="desc",
        filters={"type": [type_a, type_b]},
    )

    assert result["total"] == 2
    assert result["page"] == 2
    assert result["limit"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].id == product_2.id
    assert result["items"][0].name == "Mike Tablet"


@pytest.mark.asyncio
async def test_base_repository_remove_returns_deleted_object_and_none_when_missing(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:8]

    product = build_product(
        suffix=suffix,
        name=f"ProductoRemove_{suffix}",
        product_type="Laptop",
        description="Producto a eliminar",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    removed = await repo.remove(
        db_session,
        id=product.id,
    )

    assert removed is not None
    assert removed.id == product.id

    fetched_after_remove = await repo.get(db_session, product.id)
    assert fetched_after_remove is None

    removed_missing = await repo.remove(
        db_session,
        id=uuid4(),
    )

    assert removed_missing is None


@pytest.mark.asyncio
async def test_base_repository_soft_remove_marks_product_deleted_and_applies_kwargs(db_session):
    repo = BaseRepository(Product)
    suffix = uuid4().hex[:8]

    product = build_product(
        suffix=suffix,
        name=f"ProductoSoft_{suffix}",
        product_type="Laptop",
        description="Producto con borrado lógico",
        status=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)

    result = await repo.soft_remove(
        db_session,
        id=product.id,
        status=False,
    )

    assert result is not None
    assert result.id == product.id
    assert result.is_deleted is True
    assert result.deleted_at is not None
    assert result.status is False


@pytest.mark.asyncio
async def test_base_repository_soft_remove_marks_user_deleted_inactive_and_applies_kwargs(db_session):
    repo = BaseRepository(User)
    suffix = uuid4().hex[:8]
    deleter_id = uuid4()

    user = build_user(suffix=suffix)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    result = await repo.soft_remove(
        db_session,
        id=user.id,
        deleted_by=deleter_id,
        deactivation_reason="Incumplimiento de políticas",
    )

    assert result is not None
    assert result.id == user.id
    assert result.is_deleted is True
    assert result.deleted_at is not None
    assert result.is_active is False
    assert result.deleted_by == deleter_id
    assert result.deactivation_reason == "Incumplimiento de políticas"


@pytest.mark.asyncio
async def test_base_repository_soft_remove_returns_none_when_object_does_not_exist(db_session):
    repo = BaseRepository(User)

    result = await repo.soft_remove(
        db_session,
        id=uuid4(),
        deactivation_reason="No existe",
    )

    assert result is None