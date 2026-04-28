from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.auth import CurrentUser
from app.services.audit_log_service import AuditLogService


def build_current_user(
    *,
    user_id=None,
    username: str = "maya",
    email: str = "maya@example.com",
    is_superuser: bool = False,
    is_active: bool = True,
    role: str = "user",
) -> CurrentUser:
    return CurrentUser(
        id=user_id or uuid4(),
        username=username,
        email=email,
        is_superuser=is_superuser,
        is_active=is_active,
        role=role,
    )


@pytest.fixture
def audit_log_repository():
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_multi = AsyncMock()
    return repo


@pytest.fixture
def audit_log_service(audit_log_repository):
    return AuditLogService(audit_log_repository)


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.mark.asyncio
async def test_log_event_creates_payload_with_actor(
    audit_log_service,
    audit_log_repository,
    db_session,
):
    actor = build_current_user(role="admin", is_superuser=True)
    created_log = {"ok": True}
    audit_log_repository.create.return_value = created_log

    result = await audit_log_service.log_event(
        db_session,
        action="create_user",
        entity="user",
        entity_id="123",
        actor=actor,
        request_id="req-1",
        status="success",
        detail="Usuario creado",
    )

    assert result == created_log
    audit_log_repository.create.assert_awaited_once_with(
        db_session,
        obj_in={
            "action": "create_user",
            "entity": "user",
            "entity_id": "123",
            "actor_id": str(actor.id),
            "actor_username": actor.username,
            "actor_role": actor.role,
            "request_id": "req-1",
            "status": "success",
            "detail": "Usuario creado",
        },
    )


@pytest.mark.asyncio
async def test_log_event_creates_payload_without_actor(
    audit_log_service,
    audit_log_repository,
    db_session,
):
    created_log = {"ok": True}
    audit_log_repository.create.return_value = created_log

    result = await audit_log_service.log_event(
        db_session,
        action="login",
        entity="auth",
        entity_id=None,
        actor=None,
        request_id="req-2",
        detail="Inicio de sesión",
    )

    assert result == created_log
    audit_log_repository.create.assert_awaited_once_with(
        db_session,
        obj_in={
            "action": "login",
            "entity": "auth",
            "entity_id": None,
            "actor_id": None,
            "actor_username": None,
            "actor_role": None,
            "request_id": "req-2",
            "status": "success",
            "detail": "Inicio de sesión",
        },
    )


@pytest.mark.asyncio
async def test_get_audit_logs_passes_valid_sort_and_order(
    audit_log_service,
    audit_log_repository,
    db_session,
):
    audit_log_repository.get_multi.return_value = {"items": [], "total": 0}

    result = await audit_log_service.get_audit_logs(
        db_session,
        action="login",
        entity="auth",
        actor_username="maya",
        status="success",
        request_id="req-3",
        date_from="2026-01-01",
        date_to="2026-01-31",
        page=2,
        limit=5,
        sort_by="action",
        order="asc",
    )

    assert result == {"items": [], "total": 0}
    audit_log_repository.get_multi.assert_awaited_once_with(
        db_session,
        action="login",
        entity="auth",
        actor_username="maya",
        status="success",
        request_id="req-3",
        date_from="2026-01-01",
        date_to="2026-01-31",
        page=2,
        limit=5,
        sort_by="action",
        order="asc",
    )


@pytest.mark.asyncio
async def test_get_audit_logs_falls_back_to_created_at_when_sort_field_is_invalid(
    audit_log_service,
    audit_log_repository,
    db_session,
):
    audit_log_repository.get_multi.return_value = {"items": [], "total": 0}

    await audit_log_service.get_audit_logs(
        db_session,
        sort_by="campo_invalido",
        order="asc",
    )

    audit_log_repository.get_multi.assert_awaited_once_with(
        db_session,
        action=None,
        entity=None,
        actor_username=None,
        status=None,
        request_id=None,
        date_from=None,
        date_to=None,
        page=1,
        limit=10,
        sort_by="created_at",
        order="asc",
    )


@pytest.mark.asyncio
async def test_get_audit_logs_falls_back_to_desc_when_order_is_invalid(
    audit_log_service,
    audit_log_repository,
    db_session,
):
    audit_log_repository.get_multi.return_value = {"items": [], "total": 0}

    await audit_log_service.get_audit_logs(
        db_session,
        sort_by="status",
        order="invalido",
    )

    audit_log_repository.get_multi.assert_awaited_once_with(
        db_session,
        action=None,
        entity=None,
        actor_username=None,
        status=None,
        request_id=None,
        date_from=None,
        date_to=None,
        page=1,
        limit=10,
        sort_by="status",
        order="desc",
    )
