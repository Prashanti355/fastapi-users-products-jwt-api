from types import SimpleNamespace
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal, get_db
from app.dependencies import get_current_superuser, get_request_id
from app.main import app
from app.models.audit_log import AuditLog
from app.models.category import Category


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(AuditLog))
        await session.execute(delete(Category))
        await session.commit()

        try:
            yield session
        finally:
            await session.rollback()
            await session.execute(delete(AuditLog))
            await session.execute(delete(Category))
            await session.commit()


@pytest.fixture
def superuser():
    return SimpleNamespace(
        id=uuid4(),
        email="admin@example.com",
        username="admin",
        role="superuser",
        is_active=True,
        is_superuser=True,
    )


@pytest_asyncio.fixture
async def async_client(db_session, superuser):
    async def override_get_db():
        yield db_session

    async def override_get_current_superuser():
        return superuser

    def override_get_request_id():
        return "integration-test-request-id"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_superuser] = override_get_current_superuser
    app.dependency_overrides[get_request_id] = override_get_request_id

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


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


async def get_audit_log_by_action(db_session, *, action: str) -> AuditLog | None:
    result = await db_session.execute(select(AuditLog).where(AuditLog.action == action))
    return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_list_categories_returns_only_active_not_deleted(async_client, db_session):
    visible = await create_category_direct(
        db_session,
        name="Visible",
        slug="visible",
        is_active=True,
        is_deleted=False,
    )
    await create_category_direct(
        db_session,
        name="Inactiva",
        slug="inactiva",
        is_active=False,
        is_deleted=False,
    )
    await create_category_direct(
        db_session,
        name="Eliminada",
        slug="eliminada",
        is_active=True,
        is_deleted=True,
    )

    response = await async_client.get("/api/v1/categories")

    assert response.status_code == 200

    body = response.json()

    assert body["codigo"] == 200
    assert body["resultado"]["total"] == 1
    assert body["resultado"]["data"][0]["id"] == str(visible.id)
    assert body["resultado"]["data"][0]["name"] == "Visible"


@pytest.mark.asyncio
async def test_list_categories_filters_by_search(async_client, db_session):
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

    response = await async_client.get(
        "/api/v1/categories",
        params={"search": "dispositivos"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["resultado"]["total"] == 1
    assert body["resultado"]["data"][0]["name"] == "Electrónica"


@pytest.mark.asyncio
async def test_get_category_by_id_returns_active_category(async_client, db_session):
    category = await create_category_direct(db_session)

    response = await async_client.get(f"/api/v1/categories/{category.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["codigo"] == 200
    assert body["mensaje"] == "Categoría obtenida exitosamente."
    assert body["resultado"]["id"] == str(category.id)
    assert body["resultado"]["slug"] == "electronica"


@pytest.mark.asyncio
async def test_get_category_by_id_returns_404_for_inactive_category(async_client, db_session):
    category = await create_category_direct(
        db_session,
        name="Inactiva",
        slug="inactiva",
        is_active=False,
    )

    response = await async_client.get(f"/api/v1/categories/{category.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_category_by_id_returns_404_for_deleted_category(async_client, db_session):
    category = await create_category_direct(
        db_session,
        name="Eliminada",
        slug="eliminada",
        is_deleted=True,
    )

    response = await async_client.get(f"/api/v1/categories/{category.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_category_as_superuser(async_client, db_session):
    response = await async_client.post(
        "/api/v1/categories",
        json={
            "name": "Electrónica de Consumo",
            "description": "Productos electrónicos",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["codigo"] == 201
    assert body["mensaje"] == "Categoría creada exitosamente."
    assert body["resultado"]["name"] == "Electrónica de Consumo"
    assert body["resultado"]["slug"] == "electronica-de-consumo"

    result = await db_session.execute(
        select(Category).where(Category.slug == "electronica-de-consumo")
    )
    category = result.scalar_one_or_none()

    assert category is not None
    assert category.name == "Electrónica de Consumo"

    audit_log = await get_audit_log_by_action(db_session, action="create_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)
    assert audit_log.request_id == "integration-test-request-id"


@pytest.mark.asyncio
async def test_create_category_rejects_duplicate_slug(async_client, db_session):
    await create_category_direct(
        db_session,
        name="Electrónica",
        slug="electronica",
    )

    response = await async_client.post(
        "/api/v1/categories",
        json={
            "name": "Otra categoría",
            "slug": "electronica",
            "description": "Slug duplicado",
            "is_active": True,
        },
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_category_as_superuser(async_client, db_session):
    category = await create_category_direct(db_session)

    response = await async_client.put(
        f"/api/v1/categories/{category.id}",
        json={
            "name": "Tecnología",
            "slug": "tecnologia",
            "description": "Categoría actualizada",
            "is_active": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría actualizada exitosamente."
    assert body["resultado"]["name"] == "Tecnología"
    assert body["resultado"]["slug"] == "tecnologia"

    audit_log = await get_audit_log_by_action(db_session, action="update_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_partial_update_category_as_superuser(async_client, db_session):
    category = await create_category_direct(db_session)

    response = await async_client.patch(
        f"/api/v1/categories/{category.id}",
        json={"name": "Hogar"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría actualizada parcialmente exitosamente."
    assert body["resultado"]["name"] == "Hogar"
    assert body["resultado"]["slug"] == "hogar"

    audit_log = await get_audit_log_by_action(
        db_session,
        action="partial_update_category",
    )

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_deactivate_category_as_superuser(async_client, db_session):
    category = await create_category_direct(db_session, is_active=True)

    response = await async_client.patch(f"/api/v1/categories/{category.id}/deactivate")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría desactivada exitosamente."
    assert body["resultado"]["is_active"] is False

    audit_log = await get_audit_log_by_action(db_session, action="deactivate_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_activate_category_as_superuser(async_client, db_session):
    category = await create_category_direct(db_session, is_active=False)

    response = await async_client.patch(f"/api/v1/categories/{category.id}/activate")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría activada exitosamente."
    assert body["resultado"]["is_active"] is True

    audit_log = await get_audit_log_by_action(db_session, action="activate_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_delete_category_as_superuser(async_client, db_session):
    category = await create_category_direct(db_session)

    response = await async_client.delete(f"/api/v1/categories/{category.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría eliminada exitosamente."
    assert body["resultado"]["is_deleted"] is True

    await db_session.refresh(category)

    assert category.is_deleted is True
    assert category.is_active is False
    assert category.deleted_at is not None

    audit_log = await get_audit_log_by_action(db_session, action="delete_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_restore_category_as_superuser(async_client, db_session):
    category = await create_category_direct(
        db_session,
        is_active=False,
        is_deleted=True,
    )

    response = await async_client.patch(f"/api/v1/categories/{category.id}/restore")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría restaurada exitosamente."
    assert body["resultado"]["is_deleted"] is False
    assert body["resultado"]["is_active"] is True

    audit_log = await get_audit_log_by_action(db_session, action="restore_category")

    assert audit_log is not None
    assert audit_log.entity == "category"
    assert audit_log.entity_id == str(category.id)


@pytest.mark.asyncio
async def test_create_category_requires_superuser(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_superuser, None)

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/categories",
            json={
                "name": "Sin permisos",
                "slug": "sin-permisos",
                "description": "No debe crearse",
                "is_active": True,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 401
