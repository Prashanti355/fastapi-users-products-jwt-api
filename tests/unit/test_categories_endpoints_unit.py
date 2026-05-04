from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.exceptions.auth_exceptions import InsufficientPermissionsException
from app.dependencies import (
    get_audit_log_service,
    get_category_service,
    get_current_superuser,
    get_request_id,
)
from app.main import app
from app.models.category import Category


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
def db_marker():
    return object()


@pytest.fixture
def category_service_mock():
    service = SimpleNamespace()
    service.get_multi_categories = AsyncMock()
    service.get_public_category_by_id = AsyncMock()
    service.create_category = AsyncMock()
    service.update_category = AsyncMock()
    service.activate_category = AsyncMock()
    service.deactivate_category = AsyncMock()
    service.delete_category = AsyncMock()
    service.restore_category = AsyncMock()
    return service


@pytest.fixture
def audit_log_service_mock():
    service = SimpleNamespace()
    service.log_event = AsyncMock()
    return service


@pytest.fixture
def superuser():
    return SimpleNamespace(
        id=uuid4(),
        email="admin@example.com",
        username="admin",
        is_active=True,
        is_superuser=True,
    )


@pytest.fixture
def client(
    db_marker,
    category_service_mock,
    audit_log_service_mock,
    superuser,
):
    async def override_get_db():
        yield db_marker

    async def override_get_category_service():
        return category_service_mock

    async def override_get_audit_log_service():
        return audit_log_service_mock

    async def override_get_current_superuser():
        return superuser

    def override_get_request_id():
        return "test-request-id"

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_category_service] = override_get_category_service
    app.dependency_overrides[get_audit_log_service] = override_get_audit_log_service
    app.dependency_overrides[get_current_superuser] = override_get_current_superuser
    app.dependency_overrides[get_request_id] = override_get_request_id

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_categories_returns_paged_response(client, category_service_mock, db_marker):
    category = make_category()
    category_service_mock.get_multi_categories.return_value = {
        "total": 1,
        "page": 1,
        "limit": 10,
        "items": [category],
    }

    response = client.get("/api/v1/categories")

    assert response.status_code == 200

    body = response.json()

    assert body["codigo"] == 200
    assert body["mensaje"] == "Categorías obtenidas exitosamente."
    assert body["resultado"]["total"] == 1
    assert body["resultado"]["page"] == 1
    assert body["resultado"]["limit"] == 10
    assert body["resultado"]["data"][0]["id"] == str(category.id)
    assert body["resultado"]["data"][0]["name"] == "Electrónica"

    category_service_mock.get_multi_categories.assert_awaited_once_with(
        db_marker,
        page=1,
        limit=10,
        sort_by="created_at",
        order="desc",
        search=None,
        is_active=True,
        is_deleted=False,
    )


def test_list_categories_accepts_query_params(client, category_service_mock, db_marker):
    category_service_mock.get_multi_categories.return_value = {
        "total": 0,
        "page": 2,
        "limit": 5,
        "items": [],
    }

    response = client.get(
        "/api/v1/categories",
        params={
            "page": 2,
            "limit": 5,
            "search": "hogar",
            "sort_by": "name",
            "order": "asc",
        },
    )

    assert response.status_code == 200

    category_service_mock.get_multi_categories.assert_awaited_once_with(
        db_marker,
        page=2,
        limit=5,
        sort_by="name",
        order="asc",
        search="hogar",
        is_active=True,
        is_deleted=False,
    )


def test_get_category_by_id_returns_category(client, category_service_mock, db_marker):
    category = make_category()
    category_service_mock.get_public_category_by_id.return_value = category

    response = client.get(f"/api/v1/categories/{category.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["codigo"] == 200
    assert body["mensaje"] == "Categoría obtenida exitosamente."
    assert body["resultado"]["id"] == str(category.id)
    assert body["resultado"]["slug"] == "electronica"

    category_service_mock.get_public_category_by_id.assert_awaited_once_with(
        db_marker,
        category_id=category.id,
    )


def test_create_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category()
    category_service_mock.create_category.return_value = category

    payload = {
        "name": "Electrónica",
        "slug": "electronica",
        "description": "Productos electrónicos",
        "is_active": True,
    }

    response = client.post("/api/v1/categories", json=payload)

    assert response.status_code == 201

    body = response.json()

    assert body["codigo"] == 201
    assert body["mensaje"] == "Categoría creada exitosamente."
    assert body["resultado"]["id"] == str(category.id)
    assert body["resultado"]["name"] == "Electrónica"
    assert body["resultado"]["slug"] == "electronica"

    category_service_mock.create_category.assert_awaited_once()
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="create_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Categoría creada: Electrónica",
    )


def test_create_category_rejects_request_without_token(
    db_marker,
    category_service_mock,
    audit_log_service_mock,
):
    async def override_get_db():
        yield db_marker

    async def override_get_category_service():
        return category_service_mock

    async def override_get_audit_log_service():
        return audit_log_service_mock

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_category_service] = override_get_category_service
    app.dependency_overrides[get_audit_log_service] = override_get_audit_log_service

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/categories",
            json={
                "name": "Electrónica",
                "slug": "electronica",
                "description": "Productos electrónicos",
                "is_active": True,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 401
    category_service_mock.create_category.assert_not_awaited()


def test_create_category_rejects_non_superuser(
    db_marker,
    category_service_mock,
    audit_log_service_mock,
):
    async def override_get_db():
        yield db_marker

    async def override_get_category_service():
        return category_service_mock

    async def override_get_audit_log_service():
        return audit_log_service_mock

    async def override_get_current_superuser():
        raise InsufficientPermissionsException(message="Se requieren privilegios de superusuario.")

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_category_service] = override_get_category_service
    app.dependency_overrides[get_audit_log_service] = override_get_audit_log_service
    app.dependency_overrides[get_current_superuser] = override_get_current_superuser

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/v1/categories",
            json={
                "name": "Electrónica",
                "slug": "electronica",
                "description": "Productos electrónicos",
                "is_active": True,
            },
        )

    app.dependency_overrides.clear()

    assert response.status_code == 403
    category_service_mock.create_category.assert_not_awaited()


def test_update_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(name="Tecnología", slug="tecnologia")
    category_service_mock.update_category.return_value = category

    payload = {
        "name": "Tecnología",
        "slug": "tecnologia",
        "description": "Categoría actualizada",
        "is_active": True,
    }

    response = client.put(f"/api/v1/categories/{category.id}", json=payload)

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría actualizada exitosamente."
    assert body["resultado"]["name"] == "Tecnología"

    category_service_mock.update_category.assert_awaited_once()
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="update_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Actualización completa de la categoría Tecnología",
    )


def test_partial_update_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(name="Hogar", slug="hogar")
    category_service_mock.update_category.return_value = category

    response = client.patch(
        f"/api/v1/categories/{category.id}",
        json={"name": "Hogar"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría actualizada parcialmente exitosamente."
    assert body["resultado"]["name"] == "Hogar"

    category_service_mock.update_category.assert_awaited_once()
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="partial_update_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Actualización parcial de la categoría Hogar",
    )


def test_activate_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(is_active=True)
    category_service_mock.activate_category.return_value = category

    response = client.patch(f"/api/v1/categories/{category.id}/activate")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría activada exitosamente."
    assert body["resultado"]["is_active"] is True

    category_service_mock.activate_category.assert_awaited_once_with(
        db_marker,
        category_id=category.id,
    )
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="activate_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Categoría activada: Electrónica",
    )


def test_deactivate_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(is_active=False)
    category_service_mock.deactivate_category.return_value = category

    response = client.patch(f"/api/v1/categories/{category.id}/deactivate")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría desactivada exitosamente."
    assert body["resultado"]["is_active"] is False

    category_service_mock.deactivate_category.assert_awaited_once_with(
        db_marker,
        category_id=category.id,
    )
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="deactivate_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Categoría desactivada: Electrónica",
    )


def test_delete_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(is_active=False, is_deleted=True)
    category_service_mock.delete_category.return_value = category

    response = client.delete(f"/api/v1/categories/{category.id}")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría eliminada exitosamente."
    assert body["resultado"]["is_deleted"] is True

    category_service_mock.delete_category.assert_awaited_once_with(
        db_marker,
        category_id=category.id,
    )
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="delete_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Categoría eliminada lógicamente: Electrónica",
    )


def test_restore_category_as_superuser(
    client,
    category_service_mock,
    audit_log_service_mock,
    db_marker,
    superuser,
):
    category = make_category(is_active=True, is_deleted=False)
    category_service_mock.restore_category.return_value = category

    response = client.patch(f"/api/v1/categories/{category.id}/restore")

    assert response.status_code == 200

    body = response.json()

    assert body["mensaje"] == "Categoría restaurada exitosamente."
    assert body["resultado"]["is_deleted"] is False
    assert body["resultado"]["is_active"] is True

    category_service_mock.restore_category.assert_awaited_once_with(
        db_marker,
        category_id=category.id,
    )
    audit_log_service_mock.log_event.assert_awaited_once_with(
        db_marker,
        action="restore_category",
        entity="category",
        entity_id=str(category.id),
        actor=superuser,
        request_id="test-request-id",
        detail="Categoría restaurada: Electrónica",
    )
