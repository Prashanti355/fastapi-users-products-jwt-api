from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import engine

from app.main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """
    Cliente HTTP async contra la app real de FastAPI.
    No levanta servidor externo; usa ASGITransport.
    """
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def unique_suffix() -> str:
    """
    Sufijo único por prueba para evitar colisiones
    de username, email y product_key.
    """
    return uuid4().hex[:8]


@pytest.fixture
def build_public_register_payload():
    """
    Construye payloads válidos para /auth/register
    con datos únicos por prueba.
    """
    def _build(suffix: str, **overrides: Any) -> dict[str, Any]:
        payload = {
            "first_name": "Maya",
            "last_name": f"Test{suffix}",
            "username": f"user_{suffix}",
            "email": f"user_{suffix}@example.com",
            "password": "Clave1234",
            "profile_picture": None,
            "nationality": "MX",
            "occupation": "Tester",
            "date_of_birth": "1995-01-01",
            "contact_phone_number": "5511111111",
            "gender": "Female",
            "address": "Calle Prueba",
            "address_number": "10",
            "address_interior_number": None,
            "address_complement": None,
            "address_neighborhood": "Centro",
            "address_zip_code": "01000",
            "address_city": "CDMX",
            "address_state": "CDMX",
        }
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def build_product_payload():
    """
    Construye payloads válidos para /products
    con datos únicos por prueba.
    """
    def _build(suffix: str, **overrides: Any) -> dict[str, Any]:
        payload = {
            "name": f"Producto_{suffix}",
            "type": "Laptop",
            "price": Decimal("15999.99"),
            "status": True,
            "description": f"Producto de prueba {suffix}",
            "product_key": f"PK{suffix[:6].upper()}",
            "image_link": "https://example.com/product.jpg",
        }
        payload.update(overrides)

        # Decimal puede no serializar bien en algunos contextos si se deja como Decimal
        if isinstance(payload["price"], Decimal):
            payload["price"] = float(payload["price"])

        return payload

    return _build


@pytest_asyncio.fixture
async def register_public_user(async_client: AsyncClient, build_public_register_payload):
    """
    Helper para registrar usuarios públicos.
    Devuelve response, payload usado y suffix.
    """
    async def _register(**overrides: Any):
        suffix = overrides.pop("suffix", uuid4().hex[:8])
        payload = build_public_register_payload(suffix, **overrides)

        response = await async_client.post(
            "/api/v1/auth/register",
            json=payload
        )

        return {
            "response": response,
            "payload": payload,
            "suffix": suffix,
        }

    return _register


@pytest_asyncio.fixture
async def login_user(async_client: AsyncClient):
    """
    Helper para login vía OAuth2 form.
    """
    async def _login(username: str, password: str = "Clave1234"):
        response = await async_client.post(
            "/api/v1/auth/login",
            data={
                "username": username,
                "password": password,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        return response

    return _login


@pytest_asyncio.fixture
async def get_auth_headers(login_user):
    """
    Helper que devuelve headers Bearer listos para endpoints protegidos.
    """
    async def _headers(username: str, password: str = "Clave1234") -> dict[str, str]:
        response = await login_user(username=username, password=password)
        assert response.status_code == 200, response.text

        access_token = response.json()["access_token"]

        return {
            "Authorization": f"Bearer {access_token}"
        }

    return _headers


@pytest_asyncio.fixture
async def create_and_login_user(register_public_user, get_auth_headers):
    """
    Helper de alto nivel:
    1. registra usuario público
    2. obtiene headers Bearer
    """
    async def _create_and_login(**overrides: Any):
        registration = await register_public_user(**overrides)
        response = registration["response"]
        payload = registration["payload"]

        assert response.status_code == 201, response.text

        headers = await get_auth_headers(
            username=payload["username"],
            password=payload["password"]
        )

        return {
            "registration_response": response,
            "payload": payload,
            "headers": headers,
        }

    return _create_and_login


@pytest_asyncio.fixture
async def create_product(async_client: AsyncClient, build_product_payload):
    """
    Helper para crear productos usando un token Bearer.
    """
    async def _create(headers: dict[str, str], **overrides: Any):
        suffix = overrides.pop("suffix", uuid4().hex[:8])
        payload = build_product_payload(suffix, **overrides)

        response = await async_client.post(
            "/api/v1/products",
            json=payload,
            headers=headers
        )

        return {
            "response": response,
            "payload": payload,
            "suffix": suffix,
        }

    return _create

@pytest_asyncio.fixture
async def promote_user_to_superuser():
    """
    Promueve un usuario existente a superusuario dentro de la BD real.
    Se usa en pruebas de integración para rutas administrativas.
    """
    async def _promote(username: str):
        async with AsyncSession(engine, expire_on_commit=False) as session:
            await session.execute(
                text(
                    """
                    UPDATE users
                    SET is_superuser = TRUE,
                        role = 'admin',
                        is_active = TRUE
                    WHERE username = :username
                    """
                ),
                {"username": username},
            )
            await session.commit()

    return _promote