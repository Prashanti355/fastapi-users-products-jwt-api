from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import ANY, AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.refresh_token_service import RefreshTokenService


def naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


@pytest.fixture
def refresh_token_repository():
    repo = MagicMock()
    repo.get_by_jti = AsyncMock()
    repo.revoke_by_jti = AsyncMock()
    repo.revoke_all_for_user = AsyncMock()
    repo.delete_expired_or_old_revoked = AsyncMock()
    return repo


@pytest.fixture
def refresh_token_service(refresh_token_repository):
    return RefreshTokenService(refresh_token_repository)


@pytest.fixture
def db_session():
    return MagicMock()


@pytest.mark.asyncio
async def test_get_by_jti_returns_repository_result(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_test",
        user_id=uuid4(),
        revoked_at=None,
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.get_by_jti(
        db_session,
        jti="jti_test",
    )

    assert result == db_token
    refresh_token_repository.get_by_jti.assert_awaited_once_with(
        db_session,
        jti="jti_test",
    )


@pytest.mark.asyncio
async def test_revoke_token_delegates_to_repository(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    revoked_token = SimpleNamespace(
        jti="jti_test",
        revoked_at="2026-04-16T00:00:00Z",
    )
    refresh_token_repository.revoke_by_jti.return_value = revoked_token

    result = await refresh_token_service.revoke_token(
        db_session,
        jti="jti_test",
        revoke_reason="logout",
    )

    assert result == revoked_token
    refresh_token_repository.revoke_by_jti.assert_awaited_once_with(
        db_session,
        jti="jti_test",
        revoked_at=ANY,
        revoke_reason="logout",
    )


@pytest.mark.asyncio
async def test_revoke_all_user_tokens_delegates_to_repository(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    user_id = uuid4()
    revoked_tokens = [SimpleNamespace(), SimpleNamespace()]
    refresh_token_repository.revoke_all_for_user.return_value = revoked_tokens

    result = await refresh_token_service.revoke_all_user_tokens(
        db_session,
        user_id=user_id,
        revoke_reason="logout_all",
    )

    assert result == revoked_tokens
    refresh_token_repository.revoke_all_for_user.assert_awaited_once_with(
        db_session,
        user_id=user_id,
        revoked_at=ANY,
        revoke_reason="logout_all",
    )


@pytest.mark.asyncio
async def test_delete_expired_or_old_revoked_delegates_to_repository(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    refresh_token_repository.delete_expired_or_old_revoked.return_value = 3

    result = await refresh_token_service.delete_expired_or_old_revoked(
        db_session,
        revoked_older_than_days=7,
    )

    assert result == 3
    refresh_token_repository.delete_expired_or_old_revoked.assert_awaited_once_with(
        db_session,
        revoked_older_than_days=7,
    )


@pytest.mark.asyncio
async def test_is_token_active_returns_false_when_token_does_not_exist(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    refresh_token_repository.get_by_jti.return_value = None

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_inexistente",
    )

    assert result is False
    refresh_token_repository.get_by_jti.assert_awaited_once_with(
        db_session,
        jti="jti_inexistente",
    )


@pytest.mark.asyncio
async def test_is_token_active_returns_false_when_token_is_revoked(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_revoked",
        revoked_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_revoked",
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_token_active_returns_false_when_token_is_expired_with_aware_datetime(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_expired",
        revoked_at=None,
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_expired",
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_token_active_returns_false_when_token_is_expired_with_naive_datetime(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_expired_naive",
        revoked_at=None,
        expires_at=naive_utc_now() - timedelta(minutes=1),
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_expired_naive",
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_token_active_returns_true_when_token_is_valid_with_aware_datetime(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_active",
        revoked_at=None,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_active",
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_token_active_returns_true_when_token_is_valid_with_naive_datetime(
    refresh_token_service,
    refresh_token_repository,
    db_session,
):
    db_token = SimpleNamespace(
        jti="jti_active_naive",
        revoked_at=None,
        expires_at=naive_utc_now() + timedelta(minutes=10),
    )
    refresh_token_repository.get_by_jti.return_value = db_token

    result = await refresh_token_service.is_token_active(
        db_session,
        jti="jti_active_naive",
    )

    assert result is True
