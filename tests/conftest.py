"""Shared test fixtures."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

import config.database as _db
import main as _main
from main import app


@pytest.fixture(autouse=True)
def _no_real_db(monkeypatch):
    """Block real database and NATS connections for every test.

    BlackSheep fires on_start on the first HTTP request, which calls
    init_pool()/connect_nats(). main.py imports these by name, so we
    patch the references in main's namespace (not config.database/config.nats).
    """
    monkeypatch.setattr(_main, "init_pool", AsyncMock())
    monkeypatch.setattr(_main, "close_pool", AsyncMock())
    monkeypatch.setattr(_main, "connect_nats", AsyncMock())
    monkeypatch.setattr(_main, "close_nats", AsyncMock())


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:  # type: ignore[arg-type]
        yield ac


@pytest.fixture
def mock_conn():
    """AsyncMock that simulates an asyncpg Connection."""
    return AsyncMock()


@pytest.fixture
def patch_db(mock_conn, monkeypatch):
    """Patch config.database.get_db to yield mock_conn.

    Use this fixture in tests that exercise code paths touching the DB.
    Returns the mock connection so callers can configure fetch/fetchrow
    return values and assert call counts.
    """

    @asynccontextmanager
    async def _fake_get_db():
        yield mock_conn

    monkeypatch.setattr(_db, "get_db", _fake_get_db)
    return mock_conn
