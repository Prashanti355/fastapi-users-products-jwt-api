import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.core.exceptions.auth_exceptions import InsufficientPermissionsException
from app.core.exceptions.user_exceptions import (
    InvalidCredentialsException,
    PasswordMismatchException,
    UserAlreadyActiveException,
    UserAlreadyExistsException,
    UserAlreadyInactiveException,
    UserNotDeletedException,
    UserNotFoundException,
)
from app.models.user import User
from app.schemas.auth import CurrentUser
from app.schemas.user import PasswordChangeRequest, UserPartialUpdateRequest
from app.services.user_service import UserService


class FakeSchema:
    def __init__(self, **data):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def model_dump(self, exclude_unset: bool = False):
        return self._data.copy()


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
def user_repository():
    repo = MagicMock()
    repo.get = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.get_multi_users = AsyncMock()
    return repo


@pytest.fixture
def user_service(user_repository):
    return UserService(user_repository)


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service, user_repository, db_session):
    user = build_user()
    user_repository.get.return_value = user

    result = await user_service.get_user_by_id(db_session, user_id=user.id)

    assert result == user


@pytest.mark.asyncio
async def test_get_user_by_id_raises_when_not_found(
    user_service, user_repository, db_session
):
    user_repository.get.return_value = None

    with pytest.raises(UserNotFoundException):
        await user_service.get_user_by_id(db_session, user_id=uuid4())


@pytest.mark.asyncio
async def test_create_user_success(user_service, user_repository, db_session, mocker):
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = None
    user_repository.create.return_value = build_user()
    mocker.patch(
        "app.services.user_service.get_password_hash", return_value="hashed_pw"
    )

    user_in = FakeSchema(
        first_name="Maya",
        last_name="Pena",
        username="maya",
        email="maya@example.com",
        password="Clave1234",
        role="user",
        is_active=True,
        is_superuser=False,
    )

    result = await user_service.create_user(db_session, user_in=user_in)

    assert result.username == "maya"
    user_repository.create.assert_awaited_once()
    create_payload = user_repository.create.await_args.kwargs["obj_in"]
    assert create_payload["password"] == "hashed_pw"


@pytest.mark.asyncio
async def test_create_user_raises_when_email_already_exists(
    user_service, user_repository, db_session
):
    user_repository.get_by_email.return_value = build_user(email="maya@example.com")

    user_in = FakeSchema(
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    with pytest.raises(UserAlreadyExistsException):
        await user_service.create_user(db_session, user_in=user_in)


@pytest.mark.asyncio
async def test_create_user_raises_when_username_already_exists(
    user_service, user_repository, db_session
):
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = build_user(username="maya")

    user_in = FakeSchema(
        username="maya",
        email="maya@example.com",
        password="Clave1234",
    )

    with pytest.raises(UserAlreadyExistsException):
        await user_service.create_user(db_session, user_in=user_in)


@pytest.mark.asyncio
async def test_update_user_success(user_service, user_repository, db_session, mocker):
    user = build_user(username="maya", email="maya@example.com", role="user")
    user_repository.get.return_value = user
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = None
    user_repository.update.return_value = user
    mocker.patch(
        "app.services.user_service.get_password_hash", return_value="hashed_pw"
    )

    current_user = build_current_user(user_id=user.id, is_superuser=False)

    user_in = FakeSchema(
        username="maya",
        email="maya@example.com",
        password="NuevaClave1234",
        first_name="Maya",
        last_name="Pena",
        role="user",
        is_active=True,
        is_superuser=False,
    )

    await user_service.update_user(
        db_session,
        user_id=user.id,
        user_in=user_in,
        current_user=current_user,
    )

    user_repository.update.assert_awaited_once()
    update_payload = user_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["password"] == "hashed_pw"


@pytest.mark.asyncio
async def test_update_user_raises_when_normal_user_modifies_privileged_fields(
    user_service, user_repository, db_session
):
    user = build_user(role="user", is_superuser=False, is_active=True)
    user_repository.get.return_value = user
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = None

    current_user = build_current_user(user_id=user.id, is_superuser=False)

    user_in = FakeSchema(
        username="maya",
        email="maya@example.com",
        password="NuevaClave1234",
        first_name="Maya",
        last_name="Pena",
        role="admin",
        is_active=True,
        is_superuser=False,
    )

    with pytest.raises(InsufficientPermissionsException):
        await user_service.update_user(
            db_session,
            user_id=user.id,
            user_in=user_in,
            current_user=current_user,
        )


@pytest.mark.asyncio
async def test_partial_update_user_success_for_non_privileged_fields(
    user_service, user_repository, db_session
):
    user = build_user(role="user", is_superuser=False, is_active=True)
    user_repository.get.return_value = user
    user_repository.update.return_value = user

    current_user = build_current_user(user_id=user.id, is_superuser=False)

    user_in = FakeSchema(
        occupation="Investigadora",
        address_city="Queretaro",
        email=None,
        username=None,
    )

    await user_service.partial_update_user(
        db_session,
        user_id=user.id,
        user_in=user_in,
        current_user=current_user,
    )

    user_repository.update.assert_awaited_once()
    update_payload = user_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["occupation"] == "Investigadora"
    assert update_payload["address_city"] == "Queretaro"


@pytest.mark.asyncio
async def test_partial_update_user_raises_when_normal_user_modifies_privileged_fields(
    user_service, user_repository, db_session
):
    user = build_user(role="user", is_superuser=False, is_active=True)
    user_repository.get.return_value = user

    current_user = build_current_user(user_id=user.id, is_superuser=False)

    user_in = FakeSchema(
        role="admin",
        email=None,
        username=None,
    )

    with pytest.raises(InsufficientPermissionsException):
        await user_service.partial_update_user(
            db_session,
            user_id=user.id,
            user_in=user_in,
            current_user=current_user,
        )


@pytest.mark.asyncio
async def test_change_password_success(
    user_service, user_repository, db_session, mocker
):
    user = build_user(password="hashed_pw")
    user_repository.get.return_value = user
    user_repository.update.return_value = user
    mocker.patch("app.services.user_service.verify_password", return_value=True)
    mocker.patch(
        "app.services.user_service.get_password_hash", return_value="new_hashed_pw"
    )

    password_data = SimpleNamespace(
        current_password="Clave1234",
        new_password="NuevaClave1234",
        confirm_password="NuevaClave1234",
    )

    await user_service.change_password(
        db_session,
        user_id=user.id,
        password_data=password_data,
    )

    user_repository.update.assert_awaited_once()
    update_payload = user_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["password"] == "new_hashed_pw"


@pytest.mark.asyncio
async def test_change_password_raises_when_current_password_is_invalid(
    user_service, user_repository, db_session, mocker
):
    user = build_user(password="hashed_pw")
    user_repository.get.return_value = user
    mocker.patch("app.services.user_service.verify_password", return_value=False)

    password_data = SimpleNamespace(
        current_password="Incorrecta",
        new_password="NuevaClave1234",
        confirm_password="NuevaClave1234",
    )

    with pytest.raises(InvalidCredentialsException):
        await user_service.change_password(
            db_session,
            user_id=user.id,
            password_data=password_data,
        )


@pytest.mark.asyncio
async def test_change_password_raises_when_confirmation_does_not_match(
    user_service, user_repository, db_session, mocker
):
    user = build_user(password="hashed_pw")
    user_repository.get.return_value = user
    mocker.patch("app.services.user_service.verify_password", return_value=True)

    password_data = SimpleNamespace(
        current_password="Clave1234",
        new_password="NuevaClave1234",
        confirm_password="OtraClave999",
    )

    with pytest.raises(PasswordMismatchException):
        await user_service.change_password(
            db_session,
            user_id=user.id,
            password_data=password_data,
        )


@pytest.mark.asyncio
async def test_delete_user_success(user_service, user_repository, db_session):
    user = build_user()
    user_repository.get.return_value = user
    user_repository.soft_delete.return_value = user

    await user_service.delete_user(
        db_session,
        user_id=user.id,
        deleted_by=uuid4(),
        reason="Prueba",
    )

    user_repository.soft_delete.assert_awaited_once()
    kwargs = user_repository.soft_delete.await_args.kwargs
    assert kwargs["user_id"] == user.id
    assert kwargs["deactivation_reason"] == "Prueba"


@pytest.mark.asyncio
async def test_restore_user_success(user_service, user_repository, db_session):
    user = build_user(is_deleted=True, is_active=False)
    user_repository.get.return_value = user
    user_repository.update.return_value = user

    await user_service.restore_user(db_session, user_id=user.id)

    user_repository.update.assert_awaited_once()
    update_payload = user_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["is_deleted"] is False
    assert update_payload["is_active"] is True


@pytest.mark.asyncio
async def test_restore_user_raises_when_user_was_not_deleted(
    user_service, user_repository, db_session
):
    user = build_user(is_deleted=False)
    user_repository.get.return_value = user

    with pytest.raises(UserNotDeletedException):
        await user_service.restore_user(db_session, user_id=user.id)


@pytest.mark.asyncio
async def test_activate_user_raises_when_already_active(
    user_service, user_repository, db_session
):
    user = build_user(is_active=True)
    user_repository.get.return_value = user

    with pytest.raises(UserAlreadyActiveException):
        await user_service.activate_user(db_session, user_id=user.id)


@pytest.mark.asyncio
async def test_deactivate_user_raises_when_already_inactive(
    user_service, user_repository, db_session
):
    user = build_user(is_active=False)
    user_repository.get.return_value = user

    with pytest.raises(UserAlreadyInactiveException):
        await user_service.deactivate_user(db_session, user_id=user.id)


@pytest.mark.asyncio
async def test_ensure_no_privileged_self_update_allows_superuser(user_service):
    db_obj = build_user(is_active=True, is_superuser=False, role="user")
    current_user = CurrentUser(
        id=db_obj.id,
        username="admin",
        email="admin@example.com",
        role="admin",
        is_superuser=True,
        is_active=True,
    )

    user_service._ensure_no_privileged_self_update(
        db_obj=db_obj,
        update_data={
            "is_active": False,
            "is_superuser": True,
            "role": "admin",
        },
        current_user=current_user,
    )


@pytest.mark.asyncio
async def test_partial_update_user_raises_when_email_already_exists(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(email="original@example.com", username="maya")
    user_repository.get.return_value = db_obj
    user_repository.get_by_email.return_value = build_user(
        email="duplicado@example.com",
        username="otro",
    )

    user_in = UserPartialUpdateRequest(email="duplicado@example.com")

    with pytest.raises(UserAlreadyExistsException):
        await user_service.partial_update_user(
            db_session,
            user_id=db_obj.id,
            user_in=user_in,
        )


@pytest.mark.asyncio
async def test_partial_update_user_raises_when_username_already_exists(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(email="maya@example.com", username="maya")
    user_repository.get.return_value = db_obj
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = build_user(
        email="otro@example.com",
        username="duplicado",
    )

    user_in = UserPartialUpdateRequest(username="duplicado")

    with pytest.raises(UserAlreadyExistsException):
        await user_service.partial_update_user(
            db_session,
            user_id=db_obj.id,
            user_in=user_in,
        )


@pytest.mark.asyncio
async def test_partial_update_user_hashes_password_when_present(
    user_service,
    user_repository,
    db_session,
    mocker,
):
    db_obj = build_user(password="old_hash", email="maya@example.com", username="maya")
    user_repository.get.return_value = db_obj
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = None
    user_repository.update.return_value = db_obj

    mocker.patch("app.services.user_service.get_password_hash", return_value="new_hash")

    user_in = UserPartialUpdateRequest(password="NuevaClave1234")

    await user_service.partial_update_user(
        db_session,
        user_id=db_obj.id,
        user_in=user_in,
    )

    user_repository.update.assert_awaited_once()
    update_payload = user_repository.update.await_args.kwargs["obj_in"]
    assert update_payload["password"] == "new_hash"


@pytest.mark.asyncio
async def test_change_password_raises_when_current_password_is_invalid_for_existing_user(
    user_service,
    user_repository,
    db_session,
    mocker,
):
    db_obj = build_user(password="hashed_pw")
    user_repository.get.return_value = db_obj

    mocker.patch("app.services.user_service.verify_password", return_value=False)

    password_data = PasswordChangeRequest(
        current_password="Incorrecta123",
        new_password="NuevaClave1234",
        confirm_password="NuevaClave1234",
    )

    with pytest.raises(InvalidCredentialsException):
        await user_service.change_password(
            db_session,
            user_id=db_obj.id,
            password_data=password_data,
        )


@pytest.mark.asyncio
async def test_change_password_raises_when_new_password_and_confirm_do_not_match(
    user_service,
    user_repository,
    db_session,
    mocker,
):
    db_obj = build_user(password="hashed_pw")
    user_repository.get.return_value = db_obj

    mocker.patch("app.services.user_service.verify_password", return_value=True)

    password_data = PasswordChangeRequest(
        current_password="ClaveActual123",
        new_password="NuevaClave1234",
        confirm_password="OtraClave1234",
    )

    with pytest.raises(PasswordMismatchException):
        await user_service.change_password(
            db_session,
            user_id=db_obj.id,
            password_data=password_data,
        )


@pytest.mark.asyncio
async def test_delete_user_calls_soft_delete_with_deleted_by_and_reason(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user()
    deleted_by = uuid4()

    user_repository.get.return_value = db_obj
    user_repository.soft_delete.return_value = db_obj

    result = await user_service.delete_user(
        db_session,
        user_id=db_obj.id,
        deleted_by=deleted_by,
        reason="Incumplimiento",
    )

    assert result == db_obj
    user_repository.soft_delete.assert_awaited_once_with(
        db_session,
        user_id=db_obj.id,
        deleted_by=deleted_by,
        deactivation_reason="Incumplimiento",
    )


@pytest.mark.asyncio
async def test_activate_user_updates_when_user_is_inactive(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(is_active=False)
    updated_user = build_user(is_active=True)

    user_repository.get.return_value = db_obj
    user_repository.update.return_value = updated_user

    result = await user_service.activate_user(
        db_session,
        user_id=db_obj.id,
    )

    assert result == updated_user
    user_repository.update.assert_awaited_once_with(
        db_session,
        db_obj=db_obj,
        obj_in={
            "is_active": True,
            "deactivation_reason": None,
        },
    )


@pytest.mark.asyncio
async def test_deactivate_user_updates_when_user_is_active(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(is_active=True)
    updated_user = build_user(is_active=False)

    user_repository.get.return_value = db_obj
    user_repository.update.return_value = updated_user

    result = await user_service.deactivate_user(
        db_session,
        user_id=db_obj.id,
        reason="Suspensión temporal",
    )

    assert result == updated_user
    user_repository.update.assert_awaited_once_with(
        db_session,
        db_obj=db_obj,
        obj_in={
            "is_active": False,
            "deactivation_reason": "Suspensión temporal",
        },
    )


@pytest.mark.asyncio
async def test_update_user_raises_when_email_already_exists(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(
        username="maya",
        email="maya@example.com",
        role="user",
        is_active=True,
        is_superuser=False,
    )
    user_repository.get.return_value = db_obj
    user_repository.get_by_email.return_value = build_user(
        username="otro",
        email="duplicado@example.com",
    )

    current_user = build_current_user(
        user_id=db_obj.id,
        is_superuser=False,
        role="user",
    )

    user_in = FakeSchema(
        username="maya",
        email="duplicado@example.com",
        password="NuevaClave1234",
        first_name="Maya",
        last_name="Pena",
        role="user",
        is_active=True,
        is_superuser=False,
    )

    with pytest.raises(UserAlreadyExistsException):
        await user_service.update_user(
            db_session,
            user_id=db_obj.id,
            user_in=user_in,
            current_user=current_user,
        )


@pytest.mark.asyncio
async def test_update_user_raises_when_username_already_exists(
    user_service,
    user_repository,
    db_session,
):
    db_obj = build_user(
        username="maya",
        email="maya@example.com",
        role="user",
        is_active=True,
        is_superuser=False,
    )
    user_repository.get.return_value = db_obj
    user_repository.get_by_email.return_value = None
    user_repository.get_by_username.return_value = build_user(
        username="duplicado",
        email="otro@example.com",
    )

    current_user = build_current_user(
        user_id=db_obj.id,
        is_superuser=False,
        role="user",
    )

    user_in = FakeSchema(
        username="duplicado",
        email="maya@example.com",
        password="NuevaClave1234",
        first_name="Maya",
        last_name="Pena",
        role="user",
        is_active=True,
        is_superuser=False,
    )

    with pytest.raises(UserAlreadyExistsException):
        await user_service.update_user(
            db_session,
            user_id=db_obj.id,
            user_in=user_in,
            current_user=current_user,
        )
