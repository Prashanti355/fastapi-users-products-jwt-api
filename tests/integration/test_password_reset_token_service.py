from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.core.security import get_password_hash
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.repositories.password_reset_token_repository import (
    PasswordResetTokenRepository,
)
from app.services.password_reset_token_service import (
    PasswordResetTokenService,
)


@pytest.mark.asyncio
async def test_password_reset_token_service_creates_validates_and_marks_token_used(
    db_session,
):
    suffix = uuid4().hex[:8]

    user = User(
        id=uuid4(),
        username=f"pr_{suffix}",
        email=f"password_reset_{suffix}@example.com",
        password=get_password_hash("Clave1234"),
        first_name="Maya",
        last_name="Reset",
        is_active=True,
        is_superuser=False,
        is_deleted=False,
        role="user",
        email_verified=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    repository = PasswordResetTokenRepository()
    service = PasswordResetTokenService(repository)

    db_token = await service.create_token(
        db_session,
        user_id=user.id,
        expires_in_minutes=30,
    )

    assert db_token is not None
    assert db_token.user_id == user.id
    assert db_token.used_at is None

    valid_token = await service.get_valid_token(
        db_session,
        token=db_token.token,
    )

    assert valid_token is not None
    assert valid_token.id == db_token.id

    await service.mark_as_used(
        db_session,
        password_reset_token=db_token,
    )

    used_token = await service.get_valid_token(
        db_session,
        token=db_token.token,
    )

    assert used_token is None


@pytest.mark.asyncio
async def test_password_reset_token_service_rejects_expired_token(
    db_session,
):
    suffix = uuid4().hex[:8]

    user = User(
        id=uuid4(),
        username=f"px_{suffix}",
        email=f"password_expired_{suffix}@example.com",
        password=get_password_hash("Clave1234"),
        first_name="Maya",
        last_name="Expired",
        is_active=True,
        is_superuser=False,
        is_deleted=False,
        role="user",
        email_verified=False,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    expired_token = PasswordResetToken(
        id=uuid4(),
        token=f"expired-{uuid4().hex}",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        used_at=None,
    )

    db_session.add(expired_token)
    await db_session.commit()

    repository = PasswordResetTokenRepository()
    service = PasswordResetTokenService(repository)

    valid_token = await service.get_valid_token(
        db_session,
        token=expired_token.token,
    )

    assert valid_token is None