from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions.category_exceptions import (
    CategoryAlreadyActiveException,
    CategoryAlreadyDeletedException,
    CategoryAlreadyExistsException,
    CategoryAlreadyInactiveException,
    CategoryNotDeletedException,
    CategoryNotFoundException,
    InvalidCategoryOperationException,
)
from app.models.category import Category
from app.schemas.category import (
    CategoryCreateRequest,
    CategoryPartialUpdateRequest,
    CategoryUpdateRequest,
)
from app.services.category_service import CategoryService, normalize_category_slug


def make_category(
    *,
    name: str = "Electrónica",
    slug: str = "electronica",
    is_active: bool = True,
    is_deleted: bool = False,
) -> Category:
    return Category(
        id=uuid4(),
        name=name,
        slug=slug,
        description="Categoría de prueba",
        is_active=is_active,
        is_deleted=is_deleted,
        deleted_at=None,
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
    )


@pytest.fixture
def category_repository():
    repository = AsyncMock()
    repository.get_by_name = AsyncMock(return_value=None)
    repository.get_by_slug = AsyncMock(return_value=None)
    repository.create = AsyncMock()
    repository.get = AsyncMock()
    repository.get_multi_categories = AsyncMock()
    repository.update = AsyncMock()
    repository.soft_delete = AsyncMock()
    return repository


@pytest.fixture
def category_service(category_repository):
    return CategoryService(category_repository)


def test_normalize_category_slug_removes_accents_and_formats_text():
    result = normalize_category_slug("  Electrónica de Consumo  ")

    assert result == "electronica-de-consumo"


def test_normalize_category_slug_removes_symbols():
    result = normalize_category_slug("Categoría *** Especial!!! 2026")

    assert result == "categoria-especial-2026"


@pytest.mark.asyncio
async def test_create_category_generates_slug_from_name(category_service, category_repository):
    category = make_category(name="Electrónica de Consumo", slug="electronica-de-consumo")
    category_repository.create.return_value = category

    payload = CategoryCreateRequest(
        name="Electrónica de Consumo",
        description="Productos electrónicos",
    )

    result = await category_service.create_category(None, obj_in=payload)

    category_repository.get_by_name.assert_awaited_once_with(None, name="Electrónica de Consumo")
    category_repository.get_by_slug.assert_awaited_once_with(None, slug="electronica-de-consumo")
    category_repository.create.assert_awaited_once()

    create_call = category_repository.create.await_args.kwargs["obj_in"]

    assert create_call["slug"] == "electronica-de-consumo"
    assert result == category


@pytest.mark.asyncio
async def test_create_category_normalizes_manual_slug(category_service, category_repository):
    category = make_category(name="Ropa", slug="ropa-y-accesorios")
    category_repository.create.return_value = category

    payload = CategoryCreateRequest(
        name="Ropa",
        slug="Ropa y Accesorios",
        description="Categoría de ropa",
    )

    result = await category_service.create_category(None, obj_in=payload)

    category_repository.get_by_slug.assert_awaited_once_with(None, slug="ropa-y-accesorios")

    create_call = category_repository.create.await_args.kwargs["obj_in"]

    assert create_call["slug"] == "ropa-y-accesorios"
    assert result == category


@pytest.mark.asyncio
async def test_create_category_raises_when_name_already_exists(
    category_service,
    category_repository,
):
    existing_category = make_category(name="Electrónica", slug="electronica")
    category_repository.get_by_name.return_value = existing_category

    payload = CategoryCreateRequest(
        name="Electrónica",
        description="Duplicada",
    )

    with pytest.raises(CategoryAlreadyExistsException):
        await category_service.create_category(None, obj_in=payload)

    category_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_category_raises_when_slug_already_exists(
    category_service,
    category_repository,
):
    existing_category = make_category(name="Otra categoría", slug="electronica")
    category_repository.get_by_slug.return_value = existing_category

    payload = CategoryCreateRequest(
        name="Electrónica",
        slug="electronica",
        description="Duplicada",
    )

    with pytest.raises(CategoryAlreadyExistsException):
        await category_service.create_category(None, obj_in=payload)

    category_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_category_raises_when_slug_is_empty_after_normalization(
    category_service,
    category_repository,
):
    payload = CategoryCreateRequest(
        name="---",
        slug="---",
        description="Slug inválido",
    )

    with pytest.raises(InvalidCategoryOperationException):
        await category_service.create_category(None, obj_in=payload)

    category_repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_category_by_id_returns_category(category_service, category_repository):
    category = make_category()
    category_repository.get.return_value = category

    result = await category_service.get_category_by_id(None, category_id=category.id)

    category_repository.get.assert_awaited_once_with(None, id=category.id)
    assert result == category


@pytest.mark.asyncio
async def test_get_category_by_id_raises_when_category_does_not_exist(
    category_service,
    category_repository,
):
    category_id = uuid4()
    category_repository.get.return_value = None

    with pytest.raises(CategoryNotFoundException):
        await category_service.get_category_by_id(None, category_id=category_id)


@pytest.mark.asyncio
async def test_get_category_by_id_raises_when_category_is_deleted_and_excluded(
    category_service,
    category_repository,
):
    category = make_category(is_deleted=True)
    category_repository.get.return_value = category

    with pytest.raises(CategoryNotFoundException):
        await category_service.get_category_by_id(None, category_id=category.id)


@pytest.mark.asyncio
async def test_get_category_by_id_returns_deleted_when_include_deleted_is_true(
    category_service,
    category_repository,
):
    category = make_category(is_deleted=True)
    category_repository.get.return_value = category

    result = await category_service.get_category_by_id(
        None,
        category_id=category.id,
        include_deleted=True,
    )

    assert result == category


@pytest.mark.asyncio
async def test_get_public_category_by_id_raises_when_category_is_inactive(
    category_service,
    category_repository,
):
    category = make_category(is_active=False)
    category_repository.get.return_value = category

    with pytest.raises(CategoryNotFoundException):
        await category_service.get_public_category_by_id(None, category_id=category.id)


@pytest.mark.asyncio
async def test_get_multi_categories_delegates_to_repository(
    category_service,
    category_repository,
):
    expected = {
        "total": 1,
        "page": 1,
        "limit": 10,
        "items": [make_category()],
    }
    category_repository.get_multi_categories.return_value = expected

    result = await category_service.get_multi_categories(
        None,
        page=1,
        limit=10,
        search="electronica",
    )

    category_repository.get_multi_categories.assert_awaited_once_with(
        None,
        page=1,
        limit=10,
        sort_by="created_at",
        order="desc",
        search="electronica",
        is_active=True,
        is_deleted=False,
    )
    assert result == expected


@pytest.mark.asyncio
async def test_update_category_updates_name_and_regenerates_slug(
    category_service,
    category_repository,
):
    category = make_category(name="Electrónica", slug="electronica")
    updated_category = make_category(name="Tecnología", slug="tecnologia")

    category_repository.get.return_value = category
    category_repository.get_by_name.return_value = None
    category_repository.get_by_slug.return_value = None
    category_repository.update.return_value = updated_category

    payload = CategoryPartialUpdateRequest(name="Tecnología")

    result = await category_service.update_category(None, category_id=category.id, obj_in=payload)

    category_repository.get_by_name.assert_awaited_once_with(None, name="Tecnología")
    category_repository.get_by_slug.assert_awaited_once_with(None, slug="tecnologia")

    update_call = category_repository.update.await_args.kwargs["obj_in"]

    assert update_call["name"] == "Tecnología"
    assert update_call["slug"] == "tecnologia"
    assert result == updated_category


@pytest.mark.asyncio
async def test_update_category_raises_when_new_name_already_exists(
    category_service,
    category_repository,
):
    category = make_category(name="Electrónica", slug="electronica")
    existing_category = make_category(name="Tecnología", slug="tecnologia")

    category_repository.get.return_value = category
    category_repository.get_by_name.return_value = existing_category

    payload = CategoryPartialUpdateRequest(name="Tecnología")

    with pytest.raises(CategoryAlreadyExistsException):
        await category_service.update_category(None, category_id=category.id, obj_in=payload)

    category_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_category_raises_when_new_slug_already_exists(
    category_service,
    category_repository,
):
    category = make_category(name="Electrónica", slug="electronica")
    existing_category = make_category(name="Tecnología", slug="tecnologia")

    category_repository.get.return_value = category
    category_repository.get_by_slug.return_value = existing_category

    payload = CategoryPartialUpdateRequest(slug="Tecnología")

    with pytest.raises(CategoryAlreadyExistsException):
        await category_service.update_category(None, category_id=category.id, obj_in=payload)

    category_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_category_accepts_full_update(category_service, category_repository):
    category = make_category(name="Electrónica", slug="electronica")
    updated_category = make_category(name="Hogar", slug="hogar", is_active=False)

    category_repository.get.return_value = category
    category_repository.get_by_name.return_value = None
    category_repository.get_by_slug.return_value = None
    category_repository.update.return_value = updated_category

    payload = CategoryUpdateRequest(
        name="Hogar",
        slug="hogar",
        description="Productos para el hogar",
        is_active=False,
    )

    result = await category_service.update_category(None, category_id=category.id, obj_in=payload)

    assert result == updated_category


@pytest.mark.asyncio
async def test_delete_category_soft_deletes_category(category_service, category_repository):
    category = make_category()
    deleted_category = make_category(is_active=False, is_deleted=True)

    category_repository.get.return_value = category
    category_repository.soft_delete.return_value = deleted_category

    result = await category_service.delete_category(None, category_id=category.id)

    category_repository.soft_delete.assert_awaited_once_with(None, category_id=category.id)
    assert result == deleted_category


@pytest.mark.asyncio
async def test_delete_category_raises_when_category_is_already_deleted(
    category_service,
    category_repository,
):
    category = make_category(is_deleted=True)
    category_repository.get.return_value = category

    with pytest.raises(CategoryAlreadyDeletedException):
        await category_service.delete_category(None, category_id=category.id)

    category_repository.soft_delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_restore_category_restores_deleted_category(
    category_service,
    category_repository,
):
    category = make_category(is_active=False, is_deleted=True)
    restored_category = make_category(is_active=True, is_deleted=False)

    category_repository.get.return_value = category
    category_repository.get_by_slug.return_value = category
    category_repository.update.return_value = restored_category

    result = await category_service.restore_category(None, category_id=category.id)

    update_call = category_repository.update.await_args.kwargs["obj_in"]

    assert update_call == {
        "is_deleted": False,
        "is_active": True,
        "deleted_at": None,
    }
    assert result == restored_category


@pytest.mark.asyncio
async def test_restore_category_raises_when_category_is_not_deleted(
    category_service,
    category_repository,
):
    category = make_category(is_deleted=False)
    category_repository.get.return_value = category

    with pytest.raises(CategoryNotDeletedException):
        await category_service.restore_category(None, category_id=category.id)

    category_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_category_activates_inactive_category(
    category_service,
    category_repository,
):
    category = make_category(is_active=False)
    activated_category = make_category(is_active=True)

    category_repository.get.return_value = category
    category_repository.update.return_value = activated_category

    result = await category_service.activate_category(None, category_id=category.id)

    category_repository.update.assert_awaited_once_with(
        None,
        db_obj=category,
        obj_in={"is_active": True},
    )
    assert result == activated_category


@pytest.mark.asyncio
async def test_activate_category_raises_when_category_is_deleted(
    category_service,
    category_repository,
):
    category = make_category(is_active=False, is_deleted=True)
    category_repository.get.return_value = category

    with pytest.raises(InvalidCategoryOperationException):
        await category_service.activate_category(None, category_id=category.id)

    category_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_category_raises_when_category_is_already_active(
    category_service,
    category_repository,
):
    category = make_category(is_active=True)
    category_repository.get.return_value = category

    with pytest.raises(CategoryAlreadyActiveException):
        await category_service.activate_category(None, category_id=category.id)

    category_repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_deactivate_category_deactivates_active_category(
    category_service,
    category_repository,
):
    category = make_category(is_active=True)
    deactivated_category = make_category(is_active=False)

    category_repository.get.return_value = category
    category_repository.update.return_value = deactivated_category

    result = await category_service.deactivate_category(None, category_id=category.id)

    category_repository.update.assert_awaited_once_with(
        None,
        db_obj=category,
        obj_in={"is_active": False},
    )
    assert result == deactivated_category


@pytest.mark.asyncio
async def test_deactivate_category_raises_when_category_is_already_inactive(
    category_service,
    category_repository,
):
    category = make_category(is_active=False)
    category_repository.get.return_value = category

    with pytest.raises(CategoryAlreadyInactiveException):
        await category_service.deactivate_category(None, category_id=category.id)

    category_repository.update.assert_not_awaited()
