import pytest
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app import main as main_module
from app.core.exceptions.base import AppException
from app.core.handlers.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
)
from app.core.rate_limit import limiter
from app.core.request_logging_middleware import RequestLoggingMiddleware


@pytest.mark.asyncio
async def test_lifespan_context_manager_yields_without_error():
    entered = False

    async with main_module.lifespan(main_module.app):
        entered = True

    assert entered is True


def test_app_configuration_matches_expected_values():
    assert main_module.app.title == "Users & Products API"
    assert main_module.app.version == "3.0.0"
    assert main_module.app.debug == main_module.settings.DEBUG
    assert main_module.app.swagger_ui_init_oauth == {}
    assert main_module.app.state.limiter is limiter


def test_app_registers_expected_middlewares():
    middleware_classes = {middleware.cls for middleware in main_module.app.user_middleware}

    assert RequestLoggingMiddleware in middleware_classes
    assert CORSMiddleware in middleware_classes


def test_app_registers_expected_exception_handlers():
    assert main_module.app.exception_handlers[AppException] is app_exception_handler
    assert (
        main_module.app.exception_handlers[RequestValidationError]
        is validation_exception_handler
    )
    assert (
        main_module.app.exception_handlers[RateLimitExceeded]
        is _rate_limit_exceeded_handler
    )


def test_app_includes_api_router_with_expected_prefix_routes():
    route_paths = {route.path for route in main_module.app.routes}

    assert "/api/v1/auth/login" in route_paths
    assert "/api/v1/users" in route_paths
    assert "/api/v1/products" in route_paths
    assert "/" in route_paths
    assert "/health" in route_paths


@pytest.mark.asyncio
async def test_root_returns_expected_payload():
    response = await main_module.root()

    assert response == {
        "mensaje": "¡Bienvenido a la Users & Products API!",
        "estado": "Operativa",
        "version": "3.0.0",
        "login": "/api/v1/auth/login",
    }


@pytest.mark.asyncio
async def test_health_check_returns_expected_payload():
    response = await main_module.health_check()

    assert response == {"status": "healthy"}