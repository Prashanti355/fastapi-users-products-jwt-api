from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository


def build_user(
    *,
    suffix: str,
    username: str,
    email: str,
    first_name: str,
    last_name: str,
    is_active: bool = True,
    is_superuser: bool = False,
    is_deleted: bool = False,
) -> User:
    return User(
        id=uuid4(),
        username=username,
        email=email,
        password=get_password_hash("Clave1234"),
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_superuser=is_superuser,
        is_deleted=is_deleted,
        email_verified=False,
        role="user",
    )


@pytest.mark.asyncio
async def test_user_repository_get_by_username_returns_user(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:6]

    user = build_user(
        suffix=suffix,
        username=f"u{suffix}",
        email=f"u{suffix}@example.com",
        first_name="Maya",
        last_name="Repo",
    )
    db_session.add(user)
    await db_session.commit()

    result = await repo.get_by_username(
        db_session,
        username=user.username,
    )

    assert result is not None
    assert result.id == user.id
    assert result.username == user.username


@pytest.mark.asyncio
async def test_user_repository_get_by_username_returns_none_when_missing(db_session):
    repo = UserRepository()

    result = await repo.get_by_username(
        db_session,
        username="usuario_no_existe",
    )

    assert result is None


@pytest.mark.asyncio
async def test_user_repository_get_by_email_returns_user(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:6]

    user = build_user(
        suffix=suffix,
        username=f"e{suffix}",
        email=f"e{suffix}@example.com",
        first_name="Maya",
        last_name="Email",
    )
    db_session.add(user)
    await db_session.commit()

    result = await repo.get_by_email(
        db_session,
        email=user.email,
    )

    assert result is not None
    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.asyncio
async def test_user_repository_get_by_email_returns_none_when_missing(db_session):
    repo = UserRepository()

    result = await repo.get_by_email(
        db_session,
        email="correo_no_existe@example.com",
    )

    assert result is None


@pytest.mark.asyncio
async def test_user_repository_get_multi_users_applies_default_is_deleted_filter(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:12]
    search_token = f"ln{suffix}"

    visible_user = build_user(
        suffix=suffix,
        username=f"v{suffix}",
        email=f"v{suffix}@example.com",
        first_name="Maya",
        last_name=search_token,
        is_deleted=False,
    )
    deleted_user = build_user(
        suffix=suffix,
        username=f"d{suffix}",
        email=f"d{suffix}@example.com",
        first_name="Maya",
        last_name=search_token,
        is_deleted=True,
    )

    db_session.add_all([visible_user, deleted_user])
    await db_session.commit()

    result = await repo.get_multi_users(
        db_session,
        page=1,
        limit=10,
        search=search_token,
    )

    returned_ids = {item.id for item in result["items"]}

    assert result["total"] == 1
    assert visible_user.id in returned_ids
    assert deleted_user.id not in returned_ids


@pytest.mark.asyncio
async def test_user_repository_get_multi_users_can_filter_deleted_records(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:4]
    search_token = f"del{suffix}"

    visible_user = build_user(
        suffix=suffix,
        username=f"a{suffix}",
        email=f"a{suffix}@example.com",
        first_name="Visible",
        last_name=search_token,
        is_deleted=False,
    )
    deleted_user = build_user(
        suffix=suffix,
        username=f"b{suffix}",
        email=f"b{suffix}@example.com",
        first_name="Deleted",
        last_name=search_token,
        is_deleted=True,
    )

    db_session.add_all([visible_user, deleted_user])
    await db_session.commit()

    result = await repo.get_multi_users(
        db_session,
        page=1,
        limit=10,
        search=search_token,
        is_deleted=True,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].id == deleted_user.id


@pytest.mark.asyncio
async def test_user_repository_get_multi_users_applies_is_active_search_and_sort(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:4]
    search_token = f"tok{suffix}"

    target_user = build_user(
        suffix=suffix,
        username=f"a{suffix}",
        email=f"a{suffix}@example.com",
        first_name="Alpha",
        last_name=search_token,
        is_active=True,
    )
    inactive_user = build_user(
        suffix=suffix,
        username=f"b{suffix}",
        email=f"b{suffix}@example.com",
        first_name="Beta",
        last_name=search_token,
        is_active=False,
    )
    wrong_search_user = build_user(
        suffix=suffix,
        username=f"c{suffix}",
        email=f"c{suffix}@example.com",
        first_name="Gamma",
        last_name="otro",
        is_active=True,
    )

    db_session.add_all([target_user, inactive_user, wrong_search_user])
    await db_session.commit()

    result = await repo.get_multi_users(
        db_session,
        page=1,
        limit=10,
        sort_by="username",
        order="asc",
        search=search_token,
        is_active=True,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].id == target_user.id
    assert result["items"][0].username == target_user.username


@pytest.mark.asyncio
async def test_user_repository_get_multi_users_applies_pagination(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:4]
    search_token = f"pg{suffix}"

    username_z = f"zeta_{suffix}"
    username_m = f"mike_{suffix}"
    username_a = f"alpha_{suffix}"

    user_z = build_user(
        suffix=suffix,
        username=username_z,
        email=f"z{suffix}@example.com",
        first_name="Zeta",
        last_name=search_token,
    )
    user_m = build_user(
        suffix=suffix,
        username=username_m,
        email=f"m{suffix}@example.com",
        first_name="Mike",
        last_name=search_token,
    )
    user_a = build_user(
        suffix=suffix,
        username=username_a,
        email=f"a{suffix}@example.com",
        first_name="Alpha",
        last_name=search_token,
    )

    db_session.add_all([user_z, user_m, user_a])
    await db_session.commit()

    result = await repo.get_multi_users(
        db_session,
        page=2,
        limit=1,
        sort_by="username",
        order="desc",
        search=search_token,
    )

    assert result["total"] == 3
    assert result["page"] == 2
    assert result["limit"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0].username == username_m


@pytest.mark.asyncio
async def test_user_repository_soft_delete_marks_user_deleted_inactive_and_applies_kwargs(db_session):
    repo = UserRepository()
    suffix = uuid4().hex[:6]
    deleter_id = uuid4()

    user = build_user(
        suffix=suffix,
        username=f"s{suffix}",
        email=f"s{suffix}@example.com",
        first_name="Soft",
        last_name="Delete",
        is_active=True,
        is_deleted=False,
    )
    db_session.add(user)
    await db_session.commit()

    result = await repo.soft_delete(
        db_session,
        user_id=user.id,
        deleted_by=deleter_id,
        deactivation_reason="Incumplimiento",
    )

    assert result is not None
    assert result.id == user.id
    assert result.is_deleted is True
    assert result.deleted_at is not None
    assert result.is_active is False
    assert result.deleted_by == deleter_id
    assert result.deactivation_reason == "Incumplimiento"


@pytest.mark.asyncio
async def test_user_repository_soft_delete_returns_none_when_missing(db_session):
    repo = UserRepository()

    result = await repo.soft_delete(
        db_session,
        user_id=uuid4(),
        deactivation_reason="No existe",
    )

    assert result is None


@pytest.mark.asyncio
async def test_user_repository_is_active_returns_user_flag():
    repo = UserRepository()

    active_user = build_user(
        suffix="act001",
        username="act001",
        email="act001@example.com",
        first_name="Active",
        last_name="User",
        is_active=True,
    )
    inactive_user = build_user(
        suffix="ina001",
        username="ina001",
        email="ina001@example.com",
        first_name="Inactive",
        last_name="User",
        is_active=False,
    )

    assert await repo.is_active(active_user) is True
    assert await repo.is_active(inactive_user) is False


@pytest.mark.asyncio
async def test_user_repository_is_superuser_returns_user_flag():
    repo = UserRepository()

    normal_user = build_user(
        suffix="usr001",
        username="usr001",
        email="usr001@example.com",
        first_name="Normal",
        last_name="User",
        is_superuser=False,
    )
    admin_user = build_user(
        suffix="adm001",
        username="adm001",
        email="adm001@example.com",
        first_name="Admin",
        last_name="User",
        is_superuser=True,
    )

    assert await repo.is_superuser(normal_user) is False
    assert await repo.is_superuser(admin_user) is True