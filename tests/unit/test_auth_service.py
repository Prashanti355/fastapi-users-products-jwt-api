from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions.auth_exceptions import (
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenRefreshException,
)
from app.core.exceptions.user_exceptions import UserAlreadyExistsException
from app.models.user import User
from app.schemas.auth import CurrentUser, LoginRequest, PublicRegisterRequest, TokenData
from app.services.auth_service import AuthService


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


@pytest.fixture
def user_repository():
    repo = MagicMock()
    repo.get_by_username = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get = AsyncMock()
    return repo


@pytest.fixture
def token_service():
    service = MagicMock()
    service.generate_tokens = MagicMock()
    service.verify_refresh_token = MagicMock()
    service.verify_access_token = MagicMock()
    return service


@pytest.fixture
def refresh_token_service():
    service = MagicMock()
    service.get_by_jti = AsyncMock()
    service.revoke_token = AsyncMock()
    service.revoke_all_user_tokens = AsyncMock(return_value=[SimpleNamespace(), SimpleNamespace()])
    return service


@pytest.fixture
def password_reset_token_service():
    service = MagicMock()
    service.create_token = AsyncMock()
    service.get_valid_token = AsyncMock()
    service.mark_as_used = AsyncMock()
    return service


@pytest.fixture
def email_service():
    service = MagicMock()
    service.is_configured = MagicMock(return_value=True)
    service.send_password_reset_email = MagicMock()
    return service


@pytest.fixture
def auth_service_full(
    user_repository,
    token_service,
    refresh_token_service,
    password_reset_token_service,
    email_service,
):
    return AuthService(
        user_repository,
        token_service,
        refresh_token_service=refresh_token_service,
        password_reset_token_service=password_reset_token_service,
        email_service=email_service,
    )


@pytest.fixture
def auth_service(user_repository, token_service):
    return AuthService(user_repository, token_service)


@pytest.fixture
def db_session():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_login_success(auth_service, user_repository, token_service, db_session, mocker):
    user = build_user(password="hashed_pw")
    user_repository.get_by_username.return_value = user
    token_service.generate_tokens.return_value = SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=1800,
    )
    mocker.patch("app.services.auth_service.verify_password", return_value=True)

    result = await auth_service.login(
        db_session, login_data=LoginRequest(username="maya", password="Clave1234")
    )

    assert result.access_token == "access"
    db_session.add.assert_called_once_with(user)
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once_with(user)
    token_service.generate_tokens.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_login_raises_when_user_not_found(auth_service, user_repository, db_session):
    user_repository.get_by_username.return_value = None

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(
            db_session, login_data=LoginRequest(username="maya", password="Clave1234")
        )


@pytest.mark.asyncio
async def test_login_raises_when_password_is_incorrect(
    auth_service, user_repository, db_session, mocker
):
    user_repository.get_by_username.return_value = build_user(password="hashed_pw")
    mocker.patch("app.services.auth_service.verify_password", return_value=False)

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(
            db_session, login_data=LoginRequest(username="maya", password="Clave1234")
        )


@pytest.mark.asyncio
async def test_login_raises_when_user_is_inactive(
    auth_service, user_repository, db_session, mocker
):
    user_repository.get_by_username.return_value = build_user(is_active=False)
    mocker.patch("app.services.auth_service.verify_password", return_value=True)

    with pytest.raises(InactiveUserException):
        await auth_service.login(
            db_session, login_data=LoginRequest(username="maya", password="Clave1234")
        )


@pytest.mark.asyncio
async def test_register_success(auth_service, user_repository, token_service, db_session, mocker):
    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = None
    token_service.generate_tokens.return_value = SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=1800,
    )
    mocker.patch("app.services.auth_service.get_password_hash", return_value="hashed_pw")

    user_data = PublicRegisterRequest(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    result = await auth_service.register(db_session, user_data=user_data)

    assert result.access_token == "access"
    db_session.add.assert_called_once()
    db_session.commit.assert_awaited_once()
    db_session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_raises_when_username_already_exists(
    auth_service, user_repository, db_session
):
    user_repository.get_by_username.return_value = build_user()

    user_data = PublicRegisterRequest(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    with pytest.raises(UserAlreadyExistsException):
        await auth_service.register(db_session, user_data=user_data)


@pytest.mark.asyncio
async def test_register_raises_when_email_already_exists(auth_service, user_repository, db_session):
    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = build_user(email="maya@example.com")

    user_data = PublicRegisterRequest(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    with pytest.raises(UserAlreadyExistsException):
        await auth_service.register(db_session, user_data=user_data)


@pytest.mark.asyncio
async def test_register_forces_public_user_defaults(
    auth_service, user_repository, token_service, db_session, mocker
):
    user_repository.get_by_username.return_value = None
    user_repository.get_by_email.return_value = None
    token_service.generate_tokens.return_value = SimpleNamespace(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=1800,
    )
    mocker.patch("app.services.auth_service.get_password_hash", return_value="hashed_pw")

    user_data = PublicRegisterRequest(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    await auth_service.register(db_session, user_data=user_data)

    created_user = db_session.add.call_args.args[0]
    assert created_user.is_superuser is False
    assert created_user.is_active is True
    assert created_user.is_deleted is False
    assert created_user.email_verified is False
    assert created_user.role == "user"


@pytest.mark.asyncio
async def test_refresh_token_success(auth_service, user_repository, token_service, db_session):
    user = build_user()
    token_service.verify_refresh_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user
    token_service.generate_tokens.return_value = SimpleNamespace(
        access_token="new_access",
        refresh_token="new_refresh",
        token_type="bearer",
        expires_in=1800,
    )

    result = await auth_service.refresh_token(db_session, refresh_token="refresh_token")

    assert result.access_token == "new_access"
    token_service.generate_tokens.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_refresh_token_raises_when_user_does_not_exist(
    auth_service, user_repository, token_service, db_session
):
    token_service.verify_refresh_token.return_value = TokenData(sub=str(uuid4()))
    user_repository.get.return_value = None

    with pytest.raises(TokenRefreshException):
        await auth_service.refresh_token(db_session, refresh_token="refresh_token")


@pytest.mark.asyncio
async def test_refresh_token_raises_when_user_is_inactive(
    auth_service, user_repository, token_service, db_session
):
    user = build_user(is_active=False)
    token_service.verify_refresh_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    with pytest.raises(InactiveUserException):
        await auth_service.refresh_token(db_session, refresh_token="refresh_token")


@pytest.mark.asyncio
async def test_get_current_user_success(auth_service, user_repository, token_service, db_session):
    user = build_user()
    token_service.verify_access_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    result = await auth_service.get_current_user(db_session, token="access_token")

    assert isinstance(result, CurrentUser)
    assert result.id == user.id
    assert result.username == user.username
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_does_not_exist(
    auth_service, user_repository, token_service, db_session
):
    token_service.verify_access_token.return_value = TokenData(sub=str(uuid4()))
    user_repository.get.return_value = None

    with pytest.raises(InvalidTokenException):
        await auth_service.get_current_user(db_session, token="access_token")


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_is_inactive(
    auth_service, user_repository, token_service, db_session
):
    user = build_user(is_active=False)
    token_service.verify_access_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    with pytest.raises(InactiveUserException):
        await auth_service.get_current_user(db_session, token="access_token")


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(
    auth_service_full,
    refresh_token_service,
    token_service,
    db_session,
):
    stored_token = SimpleNamespace(revoked_at=None)
    refresh_token_service.get_by_jti.return_value = stored_token
    token_service.verify_refresh_token.return_value = TokenData(
        sub=str(uuid4()),
        jti="jti_logout_test",
    )

    await auth_service_full.logout(
        db_session,
        refresh_token="refresh_token_value",
    )

    refresh_token_service.get_by_jti.assert_awaited_once_with(
        db_session,
        jti="jti_logout_test",
    )
    refresh_token_service.revoke_token.assert_awaited_once_with(
        db_session,
        jti="jti_logout_test",
        revoke_reason="logout",
    )


@pytest.mark.asyncio
async def test_logout_all_revokes_all_user_tokens(
    auth_service_full,
    refresh_token_service,
    db_session,
):
    user_id = uuid4()

    result = await auth_service_full.logout_all(
        db_session,
        user_id=user_id,
    )

    assert result == 2
    refresh_token_service.revoke_all_user_tokens.assert_awaited_once_with(
        db_session,
        user_id=user_id,
        revoke_reason="logout_all",
    )


@pytest.mark.asyncio
async def test_forgot_password_returns_none_when_user_does_not_exist(
    auth_service_full,
    user_repository,
    password_reset_token_service,
    db_session,
):
    user_repository.get_by_email.return_value = None

    result = await auth_service_full.forgot_password(
        db_session,
        email="noexiste@example.com",
    )

    assert result is None
    password_reset_token_service.create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_forgot_password_returns_none_when_user_is_inactive(
    auth_service_full,
    user_repository,
    password_reset_token_service,
    db_session,
):
    user_repository.get_by_email.return_value = build_user(is_active=False)

    result = await auth_service_full.forgot_password(
        db_session,
        email="maya@example.com",
    )

    assert result is None
    password_reset_token_service.create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_forgot_password_returns_none_when_user_is_deleted(
    auth_service_full,
    user_repository,
    password_reset_token_service,
    db_session,
):
    user_repository.get_by_email.return_value = build_user(is_deleted=True)

    result = await auth_service_full.forgot_password(
        db_session,
        email="maya@example.com",
    )

    assert result is None
    password_reset_token_service.create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_forgot_password_creates_token_and_sends_email_for_valid_user(
    auth_service_full,
    user_repository,
    password_reset_token_service,
    email_service,
    db_session,
    mocker,
):
    user = build_user()
    db_token = SimpleNamespace(token="reset_token_123")

    user_repository.get_by_email.return_value = user
    password_reset_token_service.create_token.return_value = db_token

    mocker.patch(
        "app.services.auth_service.settings.FRONTEND_RESET_PASSWORD_URL",
        "https://frontend.example.com/reset-password",
    )

    result = await auth_service_full.forgot_password(
        db_session,
        email=user.email,
    )

    assert result == user
    password_reset_token_service.create_token.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        expires_in_minutes=30,
    )
    email_service.send_password_reset_email.assert_called_once_with(
        to_email=user.email,
        reset_link="https://frontend.example.com/reset-password?token=reset_token_123",
        username=user.username,
    )


@pytest.mark.asyncio
async def test_reset_password_raises_when_token_service_is_missing(
    user_repository,
    token_service,
    db_session,
):
    service = AuthService(user_repository, token_service)

    with pytest.raises(InvalidTokenException):
        await service.reset_password(
            db_session,
            token="token_reset",
            new_password="NuevaClave1234",
        )


@pytest.mark.asyncio
async def test_reset_password_raises_when_token_is_invalid(
    auth_service_full,
    password_reset_token_service,
    db_session,
):
    password_reset_token_service.get_valid_token.return_value = None

    with pytest.raises(InvalidTokenException):
        await auth_service_full.reset_password(
            db_session,
            token="token_reset",
            new_password="NuevaClave1234",
        )


@pytest.mark.asyncio
async def test_reset_password_raises_when_user_does_not_exist(
    auth_service_full,
    password_reset_token_service,
    user_repository,
    db_session,
):
    db_token = SimpleNamespace(user_id=uuid4())
    password_reset_token_service.get_valid_token.return_value = db_token
    user_repository.get.return_value = None

    with pytest.raises(InvalidTokenException):
        await auth_service_full.reset_password(
            db_session,
            token="token_reset",
            new_password="NuevaClave1234",
        )


@pytest.mark.asyncio
async def test_reset_password_raises_when_user_is_inactive(
    auth_service_full,
    password_reset_token_service,
    user_repository,
    db_session,
):
    user = build_user(is_active=False)
    db_token = SimpleNamespace(user_id=user.id)

    password_reset_token_service.get_valid_token.return_value = db_token
    user_repository.get.return_value = user

    with pytest.raises(InactiveUserException):
        await auth_service_full.reset_password(
            db_session,
            token="token_reset",
            new_password="NuevaClave1234",
        )


@pytest.mark.asyncio
async def test_reset_password_success_hashes_password_marks_token_used_and_revokes_sessions(
    auth_service_full,
    password_reset_token_service,
    refresh_token_service,
    user_repository,
    db_session,
    mocker,
):
    user = build_user(password="old_hash")
    db_token = SimpleNamespace(user_id=user.id)

    password_reset_token_service.get_valid_token.return_value = db_token
    user_repository.get.return_value = user
    mocker.patch("app.services.auth_service.get_password_hash", return_value="new_hash")

    result = await auth_service_full.reset_password(
        db_session,
        token="token_reset",
        new_password="NuevaClave1234",
    )

    assert result == user
    assert user.password == "new_hash"

    db_session.add.assert_called_with(user)
    db_session.commit.assert_awaited()
    db_session.refresh.assert_awaited_with(user)

    password_reset_token_service.mark_as_used.assert_awaited_once_with(
        db_session,
        password_reset_token=db_token,
    )
    refresh_token_service.revoke_all_user_tokens.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        revoke_reason="password_reset",
    )


@pytest.mark.asyncio
async def test_forgot_password_creates_token_but_does_not_send_email_when_email_service_is_not_configured(
    user_repository,
    token_service,
    refresh_token_service,
    password_reset_token_service,
    db_session,
    mocker,
):
    email_service = MagicMock()
    email_service.is_configured.return_value = False
    email_service.send_password_reset_email = MagicMock()

    service = AuthService(
        user_repository,
        token_service,
        refresh_token_service=refresh_token_service,
        password_reset_token_service=password_reset_token_service,
        email_service=email_service,
    )

    user = build_user()
    db_token = SimpleNamespace(token="reset_token_123")

    user_repository.get_by_email.return_value = user
    password_reset_token_service.create_token.return_value = db_token

    mocker.patch(
        "app.services.auth_service.settings.FRONTEND_RESET_PASSWORD_URL",
        "https://frontend.example.com/reset-password",
    )

    result = await service.forgot_password(
        db_session,
        email=user.email,
    )

    assert result == user
    password_reset_token_service.create_token.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        expires_in_minutes=30,
    )
    email_service.send_password_reset_email.assert_not_called()


@pytest.mark.asyncio
async def test_forgot_password_creates_token_but_does_not_send_email_when_frontend_url_is_missing(
    auth_service_full,
    user_repository,
    password_reset_token_service,
    email_service,
    db_session,
    mocker,
):
    user = build_user()
    db_token = SimpleNamespace(token="reset_token_123")

    user_repository.get_by_email.return_value = user
    password_reset_token_service.create_token.return_value = db_token

    mocker.patch(
        "app.services.auth_service.settings.FRONTEND_RESET_PASSWORD_URL",
        None,
    )

    result = await auth_service_full.forgot_password(
        db_session,
        email=user.email,
    )

    assert result == user
    password_reset_token_service.create_token.assert_awaited_once_with(
        db_session,
        user_id=user.id,
        expires_in_minutes=30,
    )
    email_service.send_password_reset_email.assert_not_called()
