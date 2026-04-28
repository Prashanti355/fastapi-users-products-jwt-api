from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.api.v1.endpoints.users import (
    activate_user,
    change_password,
    create_user,
    deactivate_user,
    delete_user,
    get_user,
    list_users,
    partial_update_user,
    restore_user,
    update_user,
)
from app.models.user import User
from app.schemas.auth import CurrentUser


def build_user(
    *,
    username: str = "maya",
    email: str = "maya@example.com",
    password: str = "hashed_password",
    is_active: bool = True,
    is_superuser: bool = False,
    is_deleted: bool = False,
    role: str = "user",
) -> User:
    return User(
        id=uuid4(),
        username=username,
        email=email,
        password=password,
        first_name="Maya",
        last_name="Pena",
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        email_verified=False,
        role=role,
    )


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
def db_session():
    return MagicMock()


@pytest.fixture
def user_service():
    service = MagicMock()
    service.get_multi_users = AsyncMock()
    service.get_user_by_id = AsyncMock()
    service.create_user = AsyncMock()
    service.update_user = AsyncMock()
    service.partial_update_user = AsyncMock()
    service.change_password = AsyncMock()
    service.activate_user = AsyncMock()
    service.deactivate_user = AsyncMock()
    service.delete_user = AsyncMock()
    service.restore_user = AsyncMock()
    return service


@pytest.fixture
def audit_log_service():
    service = MagicMock()
    service.log_event = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_list_users_returns_paged_response(db_session, user_service):
    current_user = build_current_user(is_superuser=True, role="admin")
    user = build_user()

    user_service.get_multi_users.return_value = {
        "total": 1,
        "page": 1,
        "limit": 10,
        "data": [user],
    }

    response = await list_users(
        db=db_session,
        page=1,
        limit=10,
        sort_by="created_at",
        order="desc",
        search=None,
        is_active=None,
        user_service=user_service,
        current_user=current_user,
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuarios obtenidos correctamente."
    assert response.resultado.total == 1
    assert response.resultado.page == 1
    assert response.resultado.limit == 10
    assert len(response.resultado.data) == 1
    assert response.resultado.data[0].username == user.username


@pytest.mark.asyncio
async def test_get_user_returns_response_for_self(db_session, user_service):
    user = build_user()
    current_user = build_current_user(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    user_service.get_user_by_id.return_value = user

    response = await get_user(
        user_id=user.id,
        db=db_session,
        user_service=user_service,
        current_user=current_user,
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario obtenido correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.username == user.username


@pytest.mark.asyncio
async def test_create_user_logs_event_and_returns_response(
    db_session,
    user_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    created_user = build_user(username="nuevo", email="nuevo@example.com")
    user_in = MagicMock()

    user_service.create_user.return_value = created_user

    response = await create_user(
        user_in=user_in,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-create-user",
    )

    assert response.codigo == 201
    assert response.mensaje == "Usuario creado correctamente."
    assert response.resultado.id == created_user.id
    assert response.resultado.username == created_user.username

    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="create_user",
        entity="user",
        entity_id=str(created_user.id),
        actor=current_user,
        request_id="req-create-user",
        detail=f"Usuario creado por superusuario: {created_user.username}",
    )


@pytest.mark.asyncio
async def test_update_user_logs_event_and_returns_response(
    db_session,
    user_service,
    audit_log_service,
):
    user = build_user()
    current_user = build_current_user(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    user_in = MagicMock()
    user_service.update_user.return_value = user

    response = await update_user(
        user_id=user.id,
        user_in=user_in,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-update-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario actualizado correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.username == user.username

    user_service.update_user.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        user_in=user_in,
        current_user=current_user,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="update_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-update-user",
        detail=f"Actualización completa del usuario {user.username}",
    )


@pytest.mark.asyncio
async def test_partial_update_user_logs_event_and_returns_response(
    db_session,
    user_service,
    audit_log_service,
):
    user = build_user()
    current_user = build_current_user(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    user_in = MagicMock()
    user_service.partial_update_user.return_value = user

    response = await partial_update_user(
        user_id=user.id,
        user_in=user_in,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-partial-update-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario actualizado parcialmente."
    assert response.resultado.id == user.id
    assert response.resultado.username == user.username

    user_service.partial_update_user.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        user_in=user_in,
        current_user=current_user,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="partial_update_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-partial-update-user",
        detail=f"Actualización parcial del usuario {user.username}",
    )


@pytest.mark.asyncio
async def test_change_password_logs_event_and_returns_simple_response(
    db_session,
    user_service,
    audit_log_service,
):
    user = build_user()
    current_user = build_current_user(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    password_data = MagicMock()

    response = await change_password(
        user_id=user.id,
        password_data=password_data,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-change-password",
    )

    assert response.codigo == 200
    assert response.mensaje == "Contraseña actualizada correctamente."
    assert response.resultado == {}

    user_service.change_password.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        password_data=password_data,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="change_password",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-change-password",
        detail="Cambio de contraseña exitoso.",
    )


@pytest.mark.asyncio
async def test_activate_user_logs_event_and_returns_toggle_response(
    db_session,
    user_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    user = build_user(is_active=True)
    user_service.activate_user.return_value = user

    response = await activate_user(
        user_id=user.id,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-activate-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario activado correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.username == user.username
    assert response.resultado.is_active is True

    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="activate_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-activate-user",
        detail=f"Usuario activado: {user.username}",
    )


@pytest.mark.asyncio
async def test_deactivate_user_logs_event_and_returns_toggle_response(
    db_session,
    user_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    user = build_user(is_active=False)
    user_service.deactivate_user.return_value = user

    response = await deactivate_user(
        user_id=user.id,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-deactivate-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario desactivado correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.username == user.username
    assert response.resultado.is_active is False

    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="deactivate_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-deactivate-user",
        detail=f"Usuario desactivado: {user.username}",
    )


@pytest.mark.asyncio
async def test_delete_user_logs_event_and_returns_delete_response(
    db_session,
    user_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    user = build_user(is_deleted=True)
    user_service.delete_user.return_value = user

    response = await delete_user(
        user_id=user.id,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-delete-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario eliminado correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.is_deleted is True

    user_service.delete_user.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        deleted_by=current_user.id,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="delete_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-delete-user",
        detail=f"Usuario eliminado lógicamente: {user.username}",
    )


@pytest.mark.asyncio
async def test_restore_user_logs_event_and_returns_restore_response(
    db_session,
    user_service,
    audit_log_service,
):
    current_user = build_current_user(is_superuser=True, role="admin")
    user = build_user(is_deleted=False)
    user_service.restore_user.return_value = user

    response = await restore_user(
        user_id=user.id,
        db=db_session,
        user_service=user_service,
        audit_log_service=audit_log_service,
        current_user=current_user,
        request_id="req-restore-user",
    )

    assert response.codigo == 200
    assert response.mensaje == "Usuario restaurado correctamente."
    assert response.resultado.id == user.id
    assert response.resultado.is_deleted is False

    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="restore_user",
        entity="user",
        entity_id=str(user.id),
        actor=current_user,
        request_id="req-restore-user",
        detail=f"Usuario restaurado: {user.username}",
    )
