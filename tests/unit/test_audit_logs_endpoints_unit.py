from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.v1.endpoints.audit_logs import list_audit_logs
from app.schemas.auth import CurrentUser


def build_current_user(
    *,
    user_id=None,
    username: str = "admin",
    email: str = "admin@example.com",
    is_superuser: bool = True,
    is_active: bool = True,
    role: str = "admin",
) -> CurrentUser:
    return CurrentUser(
        id=user_id or uuid4(),
        username=username,
        email=email,
        is_superuser=is_superuser,
        is_active=is_active,
        role=role,
    )


def build_audit_log_item():
    return {
        "id": uuid4(),
        "action": "login",
        "entity": "auth",
        "entity_id": None,
        "actor_id": str(uuid4()),
        "actor_username": "maya",
        "actor_role": "user",
        "request_id": "req-1",
        "status": "success",
        "detail": "Inicio de sesión exitoso.",
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.fixture
def audit_log_service():
    service = MagicMock()
    service.get_audit_logs = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_list_audit_logs_returns_paged_response(db_session, audit_log_service):
    current_user = build_current_user()
    audit_item = build_audit_log_item()

    audit_log_service.get_audit_logs.return_value = {
        "total": 1,
        "page": 2,
        "limit": 5,
        "items": [audit_item],
    }

    response = await list_audit_logs(
        db=db_session,
        action="login",
        entity="auth",
        actor_username="maya",
        status_filter="success",
        request_id="req-1",
        date_from=None,
        date_to=None,
        page=2,
        limit=5,
        sort_by="created_at",
        order="desc",
        service=audit_log_service,
        current_user=current_user,
    )

    assert response.codigo == 200
    assert response.mensaje == "Logs de auditoría obtenidos correctamente."
    assert response.resultado.total == 1
    assert response.resultado.page == 2
    assert response.resultado.limit == 5
    assert len(response.resultado.data) == 1
    assert response.resultado.data[0].action == "login"
    assert response.resultado.data[0].entity == "auth"

    audit_log_service.get_audit_logs.assert_awaited_once_with(
        db_session,
        action="login",
        entity="auth",
        actor_username="maya",
        status="success",
        request_id="req-1",
        date_from=None,
        date_to=None,
        page=2,
        limit=5,
        sort_by="created_at",
        order="desc",
    )
