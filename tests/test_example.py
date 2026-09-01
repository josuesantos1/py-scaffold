"""Unit tests for the example app — views, service, and repository.

Isolation strategy:
- View tests: patch config.database.get_db (via patch_db fixture) AND patch
  the service function so the test controls what the view returns.
- Service tests: patch the repository function so the test controls what
  comes back, and verify the service delegates correctly.
- Repository tests: pass a pre-configured AsyncMock connection directly;
  dict literals serve as asyncpg row substitutes (asyncpg rows are dict-like).
"""

from unittest.mock import AsyncMock

from app.example import repository, service
from app.example.model import Item, ItemCreate

# ── View tests ────────────────────────────────────────────────────────────────


async def test_list_items_endpoint(client, patch_db, monkeypatch):
    fake_items = [Item(id=1, name="book", description="novel")]

    async def fake_get_items(_conn):
        return fake_items

    monkeypatch.setattr(service, "get_items", fake_get_items)

    response = await client.get("/v1/items/")
    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "book", "description": "novel"}]


async def test_get_item_endpoint(client, patch_db, monkeypatch):
    fake_item = Item(id=7, name="chair", description=None)

    async def fake_get_item(_conn, item_id):
        return fake_item if item_id == 7 else None

    monkeypatch.setattr(service, "get_item", fake_get_item)

    response = await client.get("/v1/items/7")
    assert response.status_code == 200
    assert response.json() == {"id": 7, "name": "chair", "description": None}


async def test_get_item_not_found_endpoint(client, patch_db, monkeypatch):
    async def fake_get_item(_conn, _item_id):
        return None

    monkeypatch.setattr(service, "get_item", fake_get_item)

    response = await client.get("/v1/items/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


async def test_create_item_endpoint(client, patch_db, monkeypatch):
    created = Item(id=2, name="pen", description="blue")

    async def fake_create_item(_conn, _payload):
        return created

    monkeypatch.setattr(service, "create_item", fake_create_item)

    response = await client.post("/v1/items/", json={"name": "pen", "description": "blue"})
    assert response.status_code == 201
    assert response.json() == {"id": 2, "name": "pen", "description": "blue"}


async def test_create_item_invalid_body(client, patch_db):
    response = await client.post(
        "/v1/items/", content=b"not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 422


# ── Service unit tests ────────────────────────────────────────────────────────


async def test_service_get_items_delegates_to_repository(monkeypatch):
    fake_items = [Item(id=1, name="book", description="novel")]

    async def fake_fetch_items(_conn):
        return fake_items

    monkeypatch.setattr(repository, "fetch_items", fake_fetch_items)

    result = await service.get_items(AsyncMock())

    assert result == fake_items


async def test_service_get_item_delegates_to_repository(monkeypatch):
    fake_item = Item(id=5, name="chair", description=None)

    async def fake_fetch_item(_conn, item_id):
        return fake_item if item_id == 5 else None

    monkeypatch.setattr(repository, "fetch_item", fake_fetch_item)

    assert await service.get_item(AsyncMock(), 5) == fake_item
    assert await service.get_item(AsyncMock(), 999) is None


async def test_service_create_item_delegates_to_repository(monkeypatch):
    created = Item(id=42, name="lamp", description="desk")

    async def fake_insert_item(_conn, _payload):
        return created

    monkeypatch.setattr(repository, "insert_item", fake_insert_item)

    payload = ItemCreate(name="lamp", description="desk")
    result = await service.create_item(AsyncMock(), payload)

    assert result == created


# ── Repository unit tests ───────────────────────────────────────────────────────


async def test_repository_fetch_items_returns_all():
    rows = [
        {"id": 1, "name": "book", "description": "novel"},
        {"id": 2, "name": "pen", "description": None},
    ]
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=rows)

    result = await repository.fetch_items(conn)

    assert len(result) == 2
    assert result[0] == Item(id=1, name="book", description="novel")
    assert result[1] == Item(id=2, name="pen", description=None)
    conn.fetch.assert_awaited_once()


async def test_repository_fetch_items_empty():
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])

    result = await repository.fetch_items(conn)

    assert result == []


async def test_repository_fetch_item_found():
    row = {"id": 5, "name": "chair", "description": None}
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=row)

    result = await repository.fetch_item(conn, 5)

    assert result == Item(id=5, name="chair", description=None)
    conn.fetchrow.assert_awaited_once()


async def test_repository_fetch_item_not_found():
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=None)

    result = await repository.fetch_item(conn, 999)

    assert result is None


async def test_repository_insert_item_returns_persisted_row():
    row = {"id": 42, "name": "lamp", "description": "desk"}
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=row)

    payload = ItemCreate(name="lamp", description="desk")
    result = await repository.insert_item(conn, payload)

    assert result == Item(id=42, name="lamp", description="desk")
    # Verify payload was passed to the INSERT
    call_args = conn.fetchrow.call_args
    assert "lamp" in call_args.args
    assert "desk" in call_args.args


async def test_repository_insert_item_null_description():
    row = {"id": 10, "name": "pin", "description": None}
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=row)

    payload = ItemCreate(name="pin")
    result = await repository.insert_item(conn, payload)

    assert result.description is None
