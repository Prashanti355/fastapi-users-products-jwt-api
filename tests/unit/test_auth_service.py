import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

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
        db_session,
        login_data=LoginRequest(username="maya", password="Clave1234")
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
            db_session,
            login_data=LoginRequest(username="maya", password="Clave1234")
        )


@pytest.mark.asyncio
async def test_login_raises_when_password_is_incorrect(auth_service, user_repository, db_session, mocker):
    user_repository.get_by_username.return_value = build_user(password="hashed_pw")
    mocker.patch("app.services.auth_service.verify_password", return_value=False)

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login(
            db_session,
            login_data=LoginRequest(username="maya", password="Clave1234")
        )


@pytest.mark.asyncio
async def test_login_raises_when_user_is_inactive(auth_service, user_repository, db_session, mocker):
    user_repository.get_by_username.return_value = build_user(is_active=False)
    mocker.patch("app.services.auth_service.verify_password", return_value=True)

    with pytest.raises(InactiveUserException):
        await auth_service.login(
            db_session,
            login_data=LoginRequest(username="maya", password="Clave1234")
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
async def test_register_raises_when_username_already_exists(auth_service, user_repository, db_session):
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
async def test_register_forces_public_user_defaults(auth_service, user_repository, token_service, db_session, mocker):
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

    result = await auth_service.refresh_token(
        db_session,
        refresh_token="refresh_token"
    )

    assert result.access_token == "new_access"
    token_service.generate_tokens.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_refresh_token_raises_when_user_does_not_exist(auth_service, user_repository, token_service, db_session):
    token_service.verify_refresh_token.return_value = TokenData(sub=str(uuid4()))
    user_repository.get.return_value = None

    with pytest.raises(TokenRefreshException):
        await auth_service.refresh_token(
            db_session,
            refresh_token="refresh_token"
        )


@pytest.mark.asyncio
async def test_refresh_token_raises_when_user_is_inactive(auth_service, user_repository, token_service, db_session):
    user = build_user(is_active=False)
    token_service.verify_refresh_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    with pytest.raises(InactiveUserException):
        await auth_service.refresh_token(
            db_session,
            refresh_token="refresh_token"
        )


@pytest.mark.asyncio
async def test_get_current_user_success(auth_service, user_repository, token_service, db_session):
    user = build_user()
    token_service.verify_access_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    result = await auth_service.get_current_user(
        db_session,
        token="access_token"
    )

    assert isinstance(result, CurrentUser)
    assert result.id == user.id
    assert result.username == user.username
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_does_not_exist(auth_service, user_repository, token_service, db_session):
    token_service.verify_access_token.return_value = TokenData(sub=str(uuid4()))
    user_repository.get.return_value = None

    with pytest.raises(InvalidTokenException):
        await auth_service.get_current_user(
            db_session,
            token="access_token"
        )


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_is_inactive(auth_service, user_repository, token_service, db_session):
    user = build_user(is_active=False)
    token_service.verify_access_token.return_value = TokenData(sub=str(user.id))
    user_repository.get.return_value = user

    with pytest.raises(InactiveUserException):
        await auth_service.get_current_user(
            db_session,
            token="access_token"
        )