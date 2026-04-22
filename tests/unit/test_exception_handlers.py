import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.exceptions import RequestValidationError

from app.core.handlers.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
)


@pytest.mark.asyncio
async def test_app_exception_handler_returns_expected_json_response():
    request = MagicMock()
    exc = SimpleNamespace(
        code=409,
        message="Recurso duplicado.",
        result={"field": "email"},
    )

    response = await app_exception_handler(request, exc)

    assert response.status_code == 409
    assert json.loads(response.body) == {
        "codigo": 409,
        "mensaje": "Recurso duplicado.",
        "resultado": {"field": "email"},
    }


@pytest.mark.asyncio
async def test_validation_exception_handler_returns_expected_json_response():
    request = MagicMock()
    errors = [
        {
            "type": "string_too_short",
            "loc": ["body", "password"],
            "msg": "String should have at least 8 characters",
            "input": "123",
            "ctx": {"min_length": 8},
        }
    ]
    exc = RequestValidationError(errors)

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 400
    assert json.loads(response.body) == {
        "codigo": 400,
        "mensaje": "Datos inválidos",
        "resultado": errors,
    }