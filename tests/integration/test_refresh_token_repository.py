from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository


def build_user_for_refresh_repo(suffix: str) -> User:
    return User(
        id=uuid4(),
        username=f"rt_{suffix}",
        email=f"rt_{suffix}@example.com",
        password=get_password_hash("Clave1234"),
        first_name="Maya",
        last_name="RefreshRepo",
        is_active=True,
        is_superuser=False,
        is_deleted=False,
        role="user",
        email_verified=False,
    )


@pytest.mark.asyncio
async def test_get_by_jti_returns_token_when_it_exists(db_session):
    suffix = uuid4().hex[:8]
    user = build_user_for_refresh_repo(suffix)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = RefreshToken(
        id=uuid4(),
        jti=f"jti-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=None,
    )

    db_session.add(token)
    await db_session.commit()

    repository = RefreshTokenRepository()

    result = await repository.get_by_jti(
        db_session,
        jti=token.jti,
    )

    assert result is not None
    assert result.jti == token.jti
    assert result.user_id == user.id


@pytest.mark.asyncio
async def test_get_by_jti_returns_none_when_token_does_not_exist(db_session):
    repository = RefreshTokenRepository()

    result = await repository.get_by_jti(
        db_session,
        jti="jti-que-no-existe",
    )

    assert result is None


@pytest.mark.asyncio
async def test_revoke_by_jti_marks_token_as_revoked(db_session):
    suffix = uuid4().hex[:8]
    user = build_user_for_refresh_repo(suffix)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = RefreshToken(
        id=uuid4(),
        jti=f"revoke-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=None,
    )

    db_session.add(token)
    await db_session.commit()

    repository = RefreshTokenRepository()
    revoked_at = datetime.now(UTC)

    result = await repository.revoke_by_jti(
        db_session,
        jti=token.jti,
        revoked_at=revoked_at,
        revoke_reason="logout",
    )

    assert result is not None
    assert result.jti == token.jti
    assert result.revoked_at is not None
    assert result.revoke_reason == "logout"

    reloaded = await repository.get_by_jti(
        db_session,
        jti=token.jti,
    )
    assert reloaded is not None
    assert reloaded.revoked_at is not None
    assert reloaded.revoke_reason == "logout"


@pytest.mark.asyncio
async def test_revoke_by_jti_returns_none_when_token_not_found(db_session):
    repository = RefreshTokenRepository()

    result = await repository.revoke_by_jti(
        db_session,
        jti="jti-inexistente",
        revoked_at=datetime.now(UTC),
        revoke_reason="logout",
    )

    assert result is None


@pytest.mark.asyncio
async def test_revoke_all_for_user_revokes_only_active_tokens_of_that_user(db_session):
    suffix_a = uuid4().hex[:8]
    suffix_b = uuid4().hex[:8]

    user_a = build_user_for_refresh_repo(suffix_a)
    user_b = build_user_for_refresh_repo(suffix_b)

    db_session.add(user_a)
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    active_token_1 = RefreshToken(
        id=uuid4(),
        jti=f"a1-{uuid4().hex}",
        user_id=user_a.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=None,
    )
    active_token_2 = RefreshToken(
        id=uuid4(),
        jti=f"a2-{uuid4().hex}",
        user_id=user_a.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=None,
    )
    already_revoked = RefreshToken(
        id=uuid4(),
        jti=f"a3-{uuid4().hex}",
        user_id=user_a.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=datetime.now(UTC) - timedelta(days=1),
        revoke_reason="old_reason",
    )
    other_user_token = RefreshToken(
        id=uuid4(),
        jti=f"b1-{uuid4().hex}",
        user_id=user_b.id,
        token_type="refresh",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=None,
    )

    db_session.add_all(
        [
            active_token_1,
            active_token_2,
            already_revoked,
            other_user_token,
        ]
    )
    await db_session.commit()

    repository = RefreshTokenRepository()
    revoked_at = datetime.now(UTC)

    result = await repository.revoke_all_for_user(
        db_session,
        user_id=user_a.id,
        revoked_at=revoked_at,
        revoke_reason="logout_all",
    )

    assert len(result) == 2
    returned_jtis = {token.jti for token in result}
    assert active_token_1.jti in returned_jtis
    assert active_token_2.jti in returned_jtis

    reloaded_active_1 = await repository.get_by_jti(db_session, jti=active_token_1.jti)
    reloaded_active_2 = await repository.get_by_jti(db_session, jti=active_token_2.jti)
    reloaded_already_revoked = await repository.get_by_jti(db_session, jti=already_revoked.jti)
    reloaded_other_user = await repository.get_by_jti(db_session, jti=other_user_token.jti)

    assert reloaded_active_1 is not None
    assert reloaded_active_1.revoked_at is not None
    assert reloaded_active_1.revoke_reason == "logout_all"

    assert reloaded_active_2 is not None
    assert reloaded_active_2.revoked_at is not None
    assert reloaded_active_2.revoke_reason == "logout_all"

    assert reloaded_already_revoked is not None
    assert reloaded_already_revoked.revoke_reason == "old_reason"

    assert reloaded_other_user is not None
    assert reloaded_other_user.revoked_at is None


@pytest.mark.asyncio
async def test_delete_expired_or_old_revoked_deletes_only_matching_tokens(db_session):
    suffix = uuid4().hex[:8]
    user = build_user_for_refresh_repo(suffix)

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    now = datetime.now(UTC)

    expired_token = RefreshToken(
        id=uuid4(),
        jti=f"expired-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now - timedelta(days=1),
        revoked_at=None,
    )
    old_revoked_token = RefreshToken(
        id=uuid4(),
        jti=f"old-revoked-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now + timedelta(days=7),
        revoked_at=now - timedelta(days=10),
        revoke_reason="logout",
    )
    active_token = RefreshToken(
        id=uuid4(),
        jti=f"active-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now + timedelta(days=7),
        revoked_at=None,
    )
    recent_revoked_token = RefreshToken(
        id=uuid4(),
        jti=f"recent-revoked-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now + timedelta(days=7),
        revoked_at=now - timedelta(days=2),
        revoke_reason="logout",
    )

    db_session.add_all(
        [
            expired_token,
            old_revoked_token,
            active_token,
            recent_revoked_token,
        ]
    )
    await db_session.commit()

    repository = RefreshTokenRepository()

    deleted_count = await repository.delete_expired_or_old_revoked(
        db_session,
        revoked_older_than_days=7,
    )

    assert deleted_count == 2

    assert await repository.get_by_jti(db_session, jti=expired_token.jti) is None
    assert await repository.get_by_jti(db_session, jti=old_revoked_token.jti) is None
    assert await repository.get_by_jti(db_session, jti=active_token.jti) is not None
    assert await repository.get_by_jti(db_session, jti=recent_revoked_token.jti) is not None
