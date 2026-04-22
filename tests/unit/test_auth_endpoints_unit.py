from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.api.v1.endpoints import auth as auth_endpoints
from app.models.user import User
from app.schemas.auth import (
    CurrentUser,
    ForgotPasswordRequest,
    PublicRegisterRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
)


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
def auth_service():
    service = MagicMock()
    service.login = AsyncMock()
    service.register = AsyncMock()
    service.refresh_token = AsyncMock()
    service.forgot_password = AsyncMock()
    service.reset_password = AsyncMock()
    service.get_current_user = AsyncMock()
    service.logout = AsyncMock()
    service.logout_all = AsyncMock()
    return service


@pytest.fixture
def audit_log_service():
    service = MagicMock()
    service.log_event = AsyncMock()
    return service


@pytest.fixture
def token_service():
    service = MagicMock()
    service.verify_refresh_token = MagicMock()
    return service


@pytest.fixture
def user_repository():
    repo = MagicMock()
    repo.get = AsyncMock()
    return repo


@pytest.mark.asyncio
async def test_login_logs_event_and_returns_tokens(
    db_session,
    auth_service,
    audit_log_service,
):
    tokens = TokenResponse(
        access_token="access_token_login",
        refresh_token="refresh_token_login",
        token_type="bearer",
        expires_in=1800,
    )
    current_user = build_current_user()

    auth_service.login.return_value = tokens
    auth_service.get_current_user.return_value = current_user

    form_data = SimpleNamespace(
        username="maya",
        password="Clave1234",
    )

    response = await auth_endpoints.login.__wrapped__(
        request=MagicMock(),
        response=MagicMock(),
        form_data=form_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-login",
    )

    assert response == tokens

    auth_service.login.assert_awaited_once()
    login_payload = auth_service.login.await_args.kwargs["login_data"]
    assert login_payload.username == "maya"
    assert login_payload.password == "Clave1234"

    auth_service.get_current_user.assert_awaited_once_with(
        db_session,
        token=tokens.access_token,
    )

    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="login",
        entity="auth",
        actor=current_user,
        request_id="req-login",
        detail="Inicio de sesión exitoso.",
    )


@pytest.mark.asyncio
async def test_register_logs_event_and_returns_api_response(
    db_session,
    auth_service,
    audit_log_service,
):
    tokens = TokenResponse(
        access_token="access_token_register",
        refresh_token="refresh_token_register",
        token_type="bearer",
        expires_in=1800,
    )
    current_user = build_current_user()

    auth_service.register.return_value = tokens
    auth_service.get_current_user.return_value = current_user

    user_data = PublicRegisterRequest(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    response = await auth_endpoints.register.__wrapped__(
        request=MagicMock(),
        response=MagicMock(),
        user_data=user_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-register",
    )

    assert response.codigo == 201
    assert response.mensaje == "Usuario registrado y autenticado correctamente."
    assert response.resultado.access_token == tokens.access_token
    assert response.resultado.refresh_token == tokens.refresh_token

    auth_service.register.assert_awaited_once_with(
        db_session,
        user_data=user_data,
    )
    auth_service.get_current_user.assert_awaited_once_with(
        db_session,
        token=tokens.access_token,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="register",
        entity="user",
        entity_id=str(current_user.id),
        actor=current_user,
        request_id="req-register",
        detail="Registro público de usuario exitoso.",
    )


@pytest.mark.asyncio
async def test_refresh_token_logs_event_and_returns_api_response(
    db_session,
    auth_service,
    audit_log_service,
):
    tokens = TokenResponse(
        access_token="access_token_refresh",
        refresh_token="refresh_token_refresh",
        token_type="bearer",
        expires_in=1800,
    )
    current_user = build_current_user()

    auth_service.refresh_token.return_value = tokens
    auth_service.get_current_user.return_value = current_user

    refresh_data = RefreshTokenRequest(refresh_token="refresh_token_value")

    response = await auth_endpoints.refresh_token(
        refresh_data=refresh_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-refresh",
    )

    assert response.codigo == 200
    assert response.mensaje == "Tokens renovados correctamente."
    assert response.resultado.access_token == tokens.access_token
    assert response.resultado.refresh_token == tokens.refresh_token

    auth_service.refresh_token.assert_awaited_once_with(
        db_session,
        refresh_token="refresh_token_value",
    )
    auth_service.get_current_user.assert_awaited_once_with(
        db_session,
        token=tokens.access_token,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="refresh_token",
        entity="auth",
        actor=current_user,
        request_id="req-refresh",
        detail="Renovación de tokens exitosa.",
    )


@pytest.mark.asyncio
async def test_forgot_password_logs_event_when_user_exists(
    db_session,
    auth_service,
    audit_log_service,
):
    user = build_user()
    auth_service.forgot_password.return_value = user

    forgot_data = ForgotPasswordRequest(email=user.email)

    response = await auth_endpoints.forgot_password(
        forgot_data=forgot_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-forgot-password",
    )

    assert response.codigo == 200
    assert response.mensaje == "Si el correo existe, se generó un enlace de recuperación."
    assert response.resultado == {}

    auth_service.forgot_password.assert_awaited_once_with(
        db_session,
        email=user.email,
    )
    audit_log_service.log_event.assert_awaited_once()
    log_kwargs = audit_log_service.log_event.await_args.kwargs
    assert log_kwargs["action"] == "forgot_password"
    assert log_kwargs["entity"] == "auth"
    assert log_kwargs["request_id"] == "req-forgot-password"
    assert log_kwargs["detail"] == "Solicitud de recuperación de contraseña generada."
    assert log_kwargs["actor"].id == user.id
    assert log_kwargs["actor"].username == user.username


@pytest.mark.asyncio
async def test_forgot_password_skips_audit_log_when_user_does_not_exist(
    db_session,
    auth_service,
    audit_log_service,
):
    auth_service.forgot_password.return_value = None

    forgot_data = ForgotPasswordRequest(email="noexiste@example.com")

    response = await auth_endpoints.forgot_password(
        forgot_data=forgot_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-forgot-password-none",
    )

    assert response.codigo == 200
    assert response.mensaje == "Si el correo existe, se generó un enlace de recuperación."
    assert response.resultado == {}

    auth_service.forgot_password.assert_awaited_once_with(
        db_session,
        email="noexiste@example.com",
    )
    audit_log_service.log_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_reset_password_logs_event_and_returns_simple_response(
    db_session,
    auth_service,
    audit_log_service,
):
    user = build_user()
    auth_service.reset_password.return_value = user

    reset_data = ResetPasswordRequest(
        token="token_reset_password_12345",
        new_password="NuevaClave1234",
    )

    response = await auth_endpoints.reset_password(
        reset_data=reset_data,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-reset-password",
    )

    assert response.codigo == 200
    assert response.mensaje == "Contraseña restablecida correctamente."
    assert response.resultado == {}

    auth_service.reset_password.assert_awaited_once_with(
        db_session,
        token=reset_data.token,
        new_password=reset_data.new_password,
    )
    audit_log_service.log_event.assert_awaited_once()
    log_kwargs = audit_log_service.log_event.await_args.kwargs
    assert log_kwargs["action"] == "reset_password"
    assert log_kwargs["entity"] == "auth"
    assert log_kwargs["request_id"] == "req-reset-password"
    assert log_kwargs["detail"] == "Restablecimiento de contraseña exitoso."
    assert log_kwargs["actor"].id == user.id
    assert log_kwargs["actor"].username == user.username


@pytest.mark.asyncio
async def test_me_returns_current_user_response():
    current_user = build_current_user()

    response = await auth_endpoints.me(current_user=current_user)

    assert response.codigo == 200
    assert response.mensaje == "Usuario autenticado obtenido exitosamente."
    assert response.resultado == current_user


@pytest.mark.asyncio
async def test_logout_logs_event_when_user_exists(
    db_session,
    auth_service,
    token_service,
    user_repository,
    audit_log_service,
):
    user = build_user()
    refresh_data = RefreshTokenRequest(refresh_token="refresh_token_logout")
    token_service.verify_refresh_token.return_value = SimpleNamespace(sub=str(user.id))
    user_repository.get.return_value = user

    response = await auth_endpoints.logout(
        refresh_data=refresh_data,
        db=db_session,
        auth_service=auth_service,
        token_service=token_service,
        user_repository=user_repository,
        audit_log_service=audit_log_service,
        request_id="req-logout",
    )

    assert response.codigo == 200
    assert response.mensaje == "Sesión cerrada exitosamente."
    assert response.resultado == {}

    token_service.verify_refresh_token.assert_called_once_with("refresh_token_logout")
    user_repository.get.assert_awaited_once_with(
        db_session,
        id=user.id,
    )
    auth_service.logout.assert_awaited_once_with(
        db_session,
        refresh_token="refresh_token_logout",
    )
    audit_log_service.log_event.assert_awaited_once()
    log_kwargs = audit_log_service.log_event.await_args.kwargs
    assert log_kwargs["action"] == "logout"
    assert log_kwargs["entity"] == "auth"
    assert log_kwargs["request_id"] == "req-logout"
    assert log_kwargs["detail"] == "Cierre de sesión exitoso."
    assert log_kwargs["actor"].id == user.id
    assert log_kwargs["actor"].username == user.username


@pytest.mark.asyncio
async def test_logout_skips_audit_log_when_user_does_not_exist(
    db_session,
    auth_service,
    token_service,
    user_repository,
    audit_log_service,
):
    user_id = uuid4()
    refresh_data = RefreshTokenRequest(refresh_token="refresh_token_logout_none")
    token_service.verify_refresh_token.return_value = SimpleNamespace(sub=str(user_id))
    user_repository.get.return_value = None

    response = await auth_endpoints.logout(
        refresh_data=refresh_data,
        db=db_session,
        auth_service=auth_service,
        token_service=token_service,
        user_repository=user_repository,
        audit_log_service=audit_log_service,
        request_id="req-logout-none",
    )

    assert response.codigo == 200
    assert response.mensaje == "Sesión cerrada exitosamente."
    assert response.resultado == {}

    token_service.verify_refresh_token.assert_called_once_with("refresh_token_logout_none")
    user_repository.get.assert_awaited_once_with(
        db_session,
        id=user_id,
    )
    auth_service.logout.assert_awaited_once_with(
        db_session,
        refresh_token="refresh_token_logout_none",
    )
    audit_log_service.log_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_logout_all_logs_event_and_returns_revoked_count(
    db_session,
    auth_service,
    audit_log_service,
):
    current_user = build_current_user()
    auth_service.logout_all.return_value = 3

    response = await auth_endpoints.logout_all(
        current_user=current_user,
        db=db_session,
        auth_service=auth_service,
        audit_log_service=audit_log_service,
        request_id="req-logout-all",
    )

    assert response.codigo == 200
    assert response.mensaje == "Todas las sesiones fueron cerradas exitosamente."
    assert response.resultado == {"revoked_tokens": 3}

    auth_service.logout_all.assert_awaited_once_with(
        db_session,
        user_id=current_user.id,
    )
    audit_log_service.log_event.assert_awaited_once_with(
        db_session,
        action="logout_all",
        entity="auth",
        actor=current_user,
        request_id="req-logout-all",
        detail="Cierre de todas las sesiones exitoso. Tokens revocados: 3.",
    )