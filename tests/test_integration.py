"""Integration-style tests: full request cycle through the ASGI stack.

These tests exercise the complete path from HTTP request → middleware →
BlackSheep routing → view → service → mock asyncpg connection → response.
The only thing replaced is the database connection; everything else is real.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

import config.database as _db
from main import app


@pytest.fixture
async def conn():
    return AsyncMock()


@pytest.fixture
async def integration_client(conn, monkeypatch):
    @asynccontextmanager
    async def _fake_get_db():
        yield conn

    monkeypatch.setattr(_db, "get_db", _fake_get_db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:  # type: ignore[arg-type]
        yield ac


async def test_create_item_full_cycle(integration_client, conn):
    conn.fetchrow = AsyncMock(return_value={"id": 1, "name": "sword", "description": "sharp"})

    response = await integration_client.post(
        "/v1/items/", json={"name": "sword", "description": "sharp"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "sword"
    assert body["description"] == "sharp"


async def test_list_items_full_cycle(integration_client, conn):
    conn.fetch = AsyncMock(
        return_value=[
            {"id": 1, "name": "sword", "description": "sharp"},
            {"id": 2, "name": "shield", "description": None},
        ]
    )

    response = await integration_client.get("/v1/items/")

    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["name"] == "sword"
    assert items[1]["name"] == "shield"
    assert items[1]["description"] is None


async def test_get_item_by_id_full_cycle(integration_client, conn):
    conn.fetchrow = AsyncMock(return_value={"id": 3, "name": "shield", "description": None})

    response = await integration_client.get("/v1/items/3")

    assert response.status_code == 200
    assert response.json()["name"] == "shield"


async def test_get_missing_item_returns_404(integration_client, conn):
    conn.fetchrow = AsyncMock(return_value=None)

    response = await integration_client.get("/v1/items/9999")

    assert response.status_code == 404
    assert "detail" in response.json()


async def test_request_id_header_echoed(integration_client, conn):
    """Middleware must echo X-Request-ID (or generate one) in the response."""
    conn.fetch = AsyncMock(return_value=[])

    response = await integration_client.get("/v1/items/", headers={"x-request-id": "test-abc-123"})

    assert response.headers.get("x-request-id") == "test-abc-123"


async def test_request_id_generated_when_absent(integration_client, conn):
    conn.fetch = AsyncMock(return_value=[])

    response = await integration_client.get("/v1/items/")

    rid = response.headers.get("x-request-id")
    assert rid is not None
    assert len(rid) > 0


async def test_health_endpoint(integration_client):
    response = await integration_client.get("/admin/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_ready_endpoint(integration_client):
    response = await integration_client.get("/admin/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_invalid_json_body_returns_422(integration_client):
    response = await integration_client.post(
        "/v1/items/",
        content=b"}{bad json",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
