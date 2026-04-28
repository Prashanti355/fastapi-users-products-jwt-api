import argparse
import inspect
from unittest.mock import AsyncMock

from app.scripts import cleanup_refresh_tokens


class DummySessionFactory:
    def __init__(self, db):
        self._db = db

    def __call__(self):
        db = self._db

        class _SessionContext:
            async def __aenter__(self_inner):
                return db

            async def __aexit__(self_inner, exc_type, exc, tb):
                return False

        return _SessionContext()


class DummyRefreshTokenService:
    def __init__(self, repository):
        self.repository = repository
        self.calls = []

    async def delete_expired_or_old_revoked(self, db, *, revoked_older_than_days: int):
        self.calls.append(
            {
                "db": db,
                "revoked_older_than_days": revoked_older_than_days,
            }
        )
        return 7


def test_parse_args_uses_default_value(mocker):
    mocker.patch(
        "sys.argv",
        ["cleanup_refresh_tokens.py"],
    )

    args = cleanup_refresh_tokens.parse_args()

    assert args.revoked_older_than_days == 7


def test_parse_args_accepts_custom_value(mocker):
    mocker.patch(
        "sys.argv",
        ["cleanup_refresh_tokens.py", "--revoked-older-than-days", "15"],
    )

    args = cleanup_refresh_tokens.parse_args()

    assert args.revoked_older_than_days == 15


async def test_run_cleanup_uses_service_and_returns_deleted_count(mocker):
    fake_db = object()
    service_instance = DummyRefreshTokenService(repository="repo_stub")

    sessionmaker_mock = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.sessionmaker",
        return_value=DummySessionFactory(fake_db),
    )
    refresh_repo_ctor = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.RefreshTokenRepository",
        return_value="repo_stub",
    )
    refresh_service_ctor = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.RefreshTokenService",
        return_value=service_instance,
    )

    result = await cleanup_refresh_tokens.run_cleanup(revoked_older_than_days=12)

    assert result == 7
    sessionmaker_mock.assert_called_once_with(
        cleanup_refresh_tokens.engine,
        class_=cleanup_refresh_tokens.AsyncSession,
        expire_on_commit=False,
    )
    refresh_repo_ctor.assert_called_once_with()
    refresh_service_ctor.assert_called_once_with("repo_stub")
    assert service_instance.calls == [
        {
            "db": fake_db,
            "revoked_older_than_days": 12,
        }
    ]


def test_main_parses_args_runs_cleanup_and_prints_result(mocker):
    parse_args_mock = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.parse_args",
        return_value=argparse.Namespace(revoked_older_than_days=9),
    )

    run_cleanup_mock = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.run_cleanup",
        new_callable=AsyncMock,
        return_value=4,
    )

    def fake_asyncio_run(coro):
        assert inspect.iscoroutine(coro)
        coro.close()
        return 4

    asyncio_run_mock = mocker.patch(
        "app.scripts.cleanup_refresh_tokens.asyncio.run",
        side_effect=fake_asyncio_run,
    )

    print_mock = mocker.patch("builtins.print")

    cleanup_refresh_tokens.main()

    parse_args_mock.assert_called_once_with()
    run_cleanup_mock.assert_called_once_with(revoked_older_than_days=9)
    asyncio_run_mock.assert_called_once()
    print_mock.assert_called_once_with("Refresh tokens eliminados: 4")
