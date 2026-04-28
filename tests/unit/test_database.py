from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import SQLModel

from app.core import database as database_module


class DummySessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummyConnectionContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_get_db_yields_session_and_closes_it(mocker):
    fake_session = MagicMock()
    fake_session.close = AsyncMock()

    async_session_local_mock = mocker.patch(
        "app.core.database.AsyncSessionLocal",
        return_value=DummySessionContext(fake_session),
    )

    generator = database_module.get_db()

    yielded_session = await generator.__anext__()

    assert yielded_session is fake_session
    async_session_local_mock.assert_called_once_with()

    await generator.aclose()

    fake_session.close.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_create_db_and_tables_runs_sqlmodel_metadata_create_all(mocker):
    fake_connection = MagicMock()
    fake_connection.run_sync = AsyncMock()

    fake_engine = MagicMock()
    fake_engine.begin.return_value = DummyConnectionContext(fake_connection)

    mocker.patch("app.core.database.engine", fake_engine)

    await database_module.create_db_and_tables()

    fake_engine.begin.assert_called_once_with()
    fake_connection.run_sync.assert_awaited_once_with(SQLModel.metadata.create_all)
