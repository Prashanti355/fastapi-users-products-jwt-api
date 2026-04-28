from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.refresh_token_service import RefreshTokenService


@pytest.mark.asyncio
async def test_cleanup_deletes_expired_and_old_revoked_tokens(db_session):
    suffix = uuid4().hex[:8]

    user = User(
        id=uuid4(),
        username=f"uc_{suffix}",
        email=f"user_cleanup_{suffix}@example.com",
        password=get_password_hash("Clave1234"),
        first_name="Maya",
        last_name="Cleanup",
        is_active=True,
        is_superuser=False,
        is_deleted=False,
        role="user",
        email_verified=False,
    )

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
        expires_at=now + timedelta(days=5),
        revoked_at=now - timedelta(days=10),
        revoke_reason="logout",
    )

    active_token = RefreshToken(
        id=uuid4(),
        jti=f"active-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now + timedelta(days=5),
        revoked_at=None,
    )

    recent_revoked_token = RefreshToken(
        id=uuid4(),
        jti=f"recent-revoked-{uuid4().hex}",
        user_id=user.id,
        token_type="refresh",
        expires_at=now + timedelta(days=5),
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
    service = RefreshTokenService(repository)

    deleted_count = await service.delete_expired_or_old_revoked(
        db_session,
        revoked_older_than_days=7,
    )

    assert deleted_count == 2

    remaining_expired = await repository.get_by_jti(db_session, jti=expired_token.jti)
    remaining_old_revoked = await repository.get_by_jti(db_session, jti=old_revoked_token.jti)
    remaining_active = await repository.get_by_jti(db_session, jti=active_token.jti)
    remaining_recent_revoked = await repository.get_by_jti(db_session, jti=recent_revoked_token.jti)

    assert remaining_expired is None
    assert remaining_old_revoked is None
    assert remaining_active is not None
    assert remaining_recent_revoked is not None
