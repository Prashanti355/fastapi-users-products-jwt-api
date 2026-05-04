from datetime import UTC, datetime

import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreateRequest, CategoryPartialUpdateRequest


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Category))
        await session.commit()

        try:
            yield session
        finally:
            await session.rollback()
            await session.execute(delete(Category))
            await session.commit()


@pytest.fixture
def category_repository():
    return CategoryRepository()


async def create_category_direct(
    db_session,
    *,
    name: str = "Electrónica",
    slug: str = "electronica",
    description: str | None = "Categoría de prueba",
    is_active: bool = True,
    is_deleted: bool = False,
) -> Category:
    category = Category(
        name=name,
        slug=slug,
        description=description,
        is_active=is_active,
        is_deleted=is_deleted,
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest.mark.asyncio
async def test_create_category(category_repository, db_session):
    payload = CategoryCreateRequest(
        name="Electrónica",
        slug="electronica",
        description="Productos electrónicos",
    )

    category = await category_repository.create(db_session, obj_in=payload)

    assert category.id is not None
    assert category.name == "Electrónica"
    assert category.slug == "electronica"
    assert category.description == "Productos electrónicos"
    assert category.is_active is True
    assert category.is_deleted is False
    assert category.created_at is not None
    assert category.modified_at is not None


@pytest.mark.asyncio
async def test_get_category_by_id(category_repository, db_session):
    category = await create_category_direct(db_session)

    result = await category_repository.get(db_session, id=category.id)

    assert result is not None
    assert result.id == category.id
    assert result.name == "Electrónica"


@pytest.mark.asyncio
async def test_get_by_name_returns_category(category_repository, db_session):
    category = await create_category_direct(db_session, name="Hogar", slug="hogar")

    result = await category_repository.get_by_name(db_session, name="Hogar")

    assert result is not None
    assert result.id == category.id
    assert result.slug == "hogar"


@pytest.mark.asyncio
async def test_get_by_name_returns_none_when_not_found(category_repository, db_session):
    result = await category_repository.get_by_name(db_session, name="No existe")

    assert result is None


@pytest.mark.asyncio
async def test_get_by_slug_returns_category(category_repository, db_session):
    category = await create_category_direct(db_session, name="Ropa", slug="ropa")

    result = await category_repository.get_by_slug(db_session, slug="ropa")

    assert result is not None
    assert result.id == category.id
    assert result.name == "Ropa"


@pytest.mark.asyncio
async def test_get_by_slug_returns_none_when_not_found(category_repository, db_session):
    result = await category_repository.get_by_slug(db_session, slug="no-existe")

    assert result is None


@pytest.mark.asyncio
async def test_slug_unique_constraint(category_repository, db_session):
    await create_category_direct(db_session, name="Electrónica", slug="electronica")

    duplicated = CategoryCreateRequest(
        name="Otra categoría",
        slug="electronica",
        description="Slug duplicado",
    )

    with pytest.raises(IntegrityError):
        await category_repository.create(db_session, obj_in=duplicated)


@pytest.mark.asyncio
async def test_get_multi_categories_returns_paginated_result(category_repository, db_session):
    await create_category_direct(db_session, name="Electrónica", slug="electronica")
    await create_category_direct(db_session, name="Hogar", slug="hogar")

    result = await category_repository.get_multi_categories(
        db_session,
        page=1,
        limit=10,
        sort_by="name",
        order="asc",
    )

    assert result["total"] == 2
    assert result["page"] == 1
    assert result["limit"] == 10
    assert len(result["items"]) == 2
    assert result["items"][0].name == "Electrónica"
    assert result["items"][1].name == "Hogar"


@pytest.mark.asyncio
async def test_get_multi_categories_filters_by_is_active(category_repository, db_session):
    await create_category_direct(db_session, name="Activa", slug="activa", is_active=True)
    await create_category_direct(db_session, name="Inactiva", slug="inactiva", is_active=False)

    result = await category_repository.get_multi_categories(
        db_session,
        is_active=True,
    )

    assert result["total"] == 1
    assert result["items"][0].name == "Activa"


@pytest.mark.asyncio
async def test_get_multi_categories_excludes_deleted_by_default(
    category_repository,
    db_session,
):
    await create_category_direct(db_session, name="Visible", slug="visible", is_deleted=False)
    await create_category_direct(db_session, name="Eliminada", slug="eliminada", is_deleted=True)

    result = await category_repository.get_multi_categories(db_session)

    assert result["total"] == 1
    assert result["items"][0].name == "Visible"


@pytest.mark.asyncio
async def test_get_multi_categories_can_include_deleted(category_repository, db_session):
    await create_category_direct(db_session, name="Visible", slug="visible", is_deleted=False)
    await create_category_direct(db_session, name="Eliminada", slug="eliminada", is_deleted=True)

    result = await category_repository.get_multi_categories(
        db_session,
        is_deleted=True,
    )

    assert result["total"] == 1
    assert result["items"][0].name == "Eliminada"


@pytest.mark.asyncio
async def test_get_multi_categories_filters_by_search(category_repository, db_session):
    await create_category_direct(
        db_session,
        name="Electrónica",
        slug="electronica",
        description="Dispositivos y accesorios",
    )
    await create_category_direct(
        db_session,
        name="Hogar",
        slug="hogar",
        description="Muebles y cocina",
    )

    result = await category_repository.get_multi_categories(
        db_session,
        search="dispositivos",
    )

    assert result["total"] == 1
    assert result["items"][0].name == "Electrónica"


@pytest.mark.asyncio
async def test_update_category(category_repository, db_session):
    category = await create_category_direct(db_session)

    payload = CategoryPartialUpdateRequest(
        name="Tecnología",
        slug="tecnologia",
        description="Nueva descripción",
        is_active=False,
    )

    result = await category_repository.update(
        db_session,
        db_obj=category,
        obj_in=payload,
    )

    assert result.name == "Tecnología"
    assert result.slug == "tecnologia"
    assert result.description == "Nueva descripción"
    assert result.is_active is False
    assert result.modified_at is not None


@pytest.mark.asyncio
async def test_soft_delete_category(category_repository, db_session):
    category = await create_category_direct(db_session)

    result = await category_repository.soft_delete(
        db_session,
        category_id=category.id,
    )

    assert result is not None
    assert result.id == category.id
    assert result.is_deleted is True
    assert result.is_active is False
    assert result.deleted_at is not None


@pytest.mark.asyncio
async def test_soft_delete_returns_none_when_category_does_not_exist(
    category_repository,
    db_session,
):
    result = await category_repository.soft_delete(
        db_session,
        category_id="00000000-0000-0000-0000-000000000000",
    )

    assert result is None


@pytest.mark.asyncio
async def test_remove_category(category_repository, db_session):
    category = await create_category_direct(db_session)

    removed = await category_repository.remove(db_session, id=category.id)
    result = await category_repository.get(db_session, id=category.id)

    assert removed is not None
    assert removed.id == category.id
    assert result is None


@pytest.mark.asyncio
async def test_update_accepts_dict(category_repository, db_session):
    category = await create_category_direct(db_session)

    result = await category_repository.update(
        db_session,
        db_obj=category,
        obj_in={
            "name": "Actualizada",
            "slug": "actualizada",
            "modified_at": datetime.now(UTC),
        },
    )

    assert result.name == "Actualizada"
    assert result.slug == "actualizada"
