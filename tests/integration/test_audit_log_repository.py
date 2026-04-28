from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.repositories.audit_log_repository import AuditLogRepository


def build_audit_log_payload(
    *,
    action: str,
    entity: str,
    actor_username: str,
    status: str,
    request_id: str,
    created_at: datetime,
) -> dict:
    return {
        "id": uuid4(),
        "action": action,
        "entity": entity,
        "entity_id": str(uuid4()),
        "actor_id": str(uuid4()),
        "actor_username": actor_username,
        "actor_role": "admin",
        "request_id": request_id,
        "status": status,
        "detail": f"Detalle {action} {entity}",
        "created_at": created_at,
    }


@pytest.mark.asyncio
async def test_audit_log_repository_create_persists_and_returns_log(db_session):
    repo = AuditLogRepository()
    now_utc = datetime.now(timezone.utc)
    payload = build_audit_log_payload(
        action="login",
        entity="auth",
        actor_username="maya",
        status="success",
        request_id=f"req-{uuid4().hex[:8]}",
        created_at=now_utc,
    )

    created = await repo.create(
        db_session,
        obj_in=payload,
    )

    assert created.id == payload["id"]
    assert created.action == "login"
    assert created.entity == "auth"
    assert created.actor_username == "maya"
    assert created.status == "success"
    assert created.request_id == payload["request_id"]
    assert created.created_at == now_utc


@pytest.mark.asyncio
async def test_audit_log_repository_get_multi_without_filters_returns_paginated_results(
    db_session,
):
    repo = AuditLogRepository()
    base_time = datetime.now(timezone.utc)

    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="login",
            entity="auth",
            actor_username="maya_a",
            status="success",
            request_id=f"req-{uuid4().hex[:8]}",
            created_at=base_time - timedelta(minutes=3),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="create_product",
            entity="product",
            actor_username="maya_b",
            status="success",
            request_id=f"req-{uuid4().hex[:8]}",
            created_at=base_time - timedelta(minutes=2),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="delete_user",
            entity="user",
            actor_username="maya_c",
            status="error",
            request_id=f"req-{uuid4().hex[:8]}",
            created_at=base_time - timedelta(minutes=1),
        ),
    )

    result = await repo.get_multi(
        db_session,
        page=1,
        limit=2,
    )

    assert result["total"] >= 3
    assert result["page"] == 1
    assert result["limit"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0].created_at >= result["items"][1].created_at


@pytest.mark.asyncio
async def test_audit_log_repository_get_multi_applies_all_supported_filters(db_session):
    repo = AuditLogRepository()
    base_time = datetime.now(timezone.utc)
    suffix = uuid4().hex[:6]

    target_request_id = f"req-{suffix}"
    target_actor = f"maya_{suffix}"
    target_from = base_time - timedelta(minutes=10)
    target_to = base_time - timedelta(minutes=1)

    target_log = await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="refresh_token",
            entity="auth",
            actor_username=target_actor,
            status="success",
            request_id=target_request_id,
            created_at=base_time - timedelta(minutes=5),
        ),
    )

    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="refresh_token",
            entity="auth",
            actor_username=target_actor,
            status="error",
            request_id=f"req-other-{suffix}",
            created_at=base_time - timedelta(minutes=4),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="login",
            entity="auth",
            actor_username=target_actor,
            status="success",
            request_id=f"req-login-{suffix}",
            created_at=base_time - timedelta(minutes=5),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="refresh_token",
            entity="user",
            actor_username=target_actor,
            status="success",
            request_id=f"req-user-{suffix}",
            created_at=base_time - timedelta(minutes=5),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="refresh_token",
            entity="auth",
            actor_username=f"other_{suffix}",
            status="success",
            request_id=f"req-actor-{suffix}",
            created_at=base_time - timedelta(minutes=5),
        ),
    )
    await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="refresh_token",
            entity="auth",
            actor_username=target_actor,
            status="success",
            request_id=f"req-old-{suffix}",
            created_at=base_time - timedelta(days=3),
        ),
    )

    result = await repo.get_multi(
        db_session,
        action="refresh_token",
        entity="auth",
        actor_username=target_actor,
        status="success",
        request_id=target_request_id,
        date_from=target_from,
        date_to=target_to,
        page=1,
        limit=10,
        sort_by="created_at",
        order="desc",
    )

    assert result["total"] == 1
    assert result["page"] == 1
    assert result["limit"] == 10
    assert len(result["items"]) == 1
    assert result["items"][0].id == target_log.id
    assert result["items"][0].request_id == target_request_id


@pytest.mark.asyncio
async def test_audit_log_repository_get_multi_supports_alternate_sort_fields_and_ascending_order(
    db_session,
):
    repo = AuditLogRepository()
    base_time = datetime.now(timezone.utc)
    suffix = uuid4().hex[:6]
    shared_request_id = f"req-sort-{suffix}"

    log_b = await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="update_user",
            entity="user",
            actor_username=f"bravo_{suffix}",
            status="success",
            request_id=shared_request_id,
            created_at=base_time - timedelta(minutes=2),
        ),
    )
    log_a = await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="update_user",
            entity="user",
            actor_username=f"alpha_{suffix}",
            status="success",
            request_id=shared_request_id,
            created_at=base_time - timedelta(minutes=1),
        ),
    )

    result = await repo.get_multi(
        db_session,
        action="update_user",
        entity="user",
        request_id=shared_request_id,
        page=1,
        limit=10,
        sort_by="actor_username",
        order="asc",
    )

    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0].id == log_a.id
    assert result["items"][0].actor_username == f"alpha_{suffix}"
    assert result["items"][1].id == log_b.id
    assert result["items"][1].actor_username == f"bravo_{suffix}"


@pytest.mark.asyncio
async def test_audit_log_repository_get_multi_falls_back_to_created_at_when_sort_field_is_invalid(
    db_session,
):
    repo = AuditLogRepository()
    base_time = datetime.now(timezone.utc)
    suffix = uuid4().hex[:6]

    older = await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="logout",
            entity="auth",
            actor_username=f"user_old_{suffix}",
            status="success",
            request_id=f"req-old-{suffix}",
            created_at=base_time - timedelta(minutes=2),
        ),
    )
    newer = await repo.create(
        db_session,
        obj_in=build_audit_log_payload(
            action="logout",
            entity="auth",
            actor_username=f"user_new_{suffix}",
            status="success",
            request_id=f"req-new-{suffix}",
            created_at=base_time - timedelta(minutes=1),
        ),
    )

    result = await repo.get_multi(
        db_session,
        action="logout",
        entity="auth",
        page=1,
        limit=10,
        sort_by="campo_invalido",
        order="desc",
    )

    filtered_items = [
        item for item in result["items"] if item.id in {older.id, newer.id}
    ]

    assert len(filtered_items) == 2
    assert filtered_items[0].id == newer.id
    assert filtered_items[1].id == older.id
