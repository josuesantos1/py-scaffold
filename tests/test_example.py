from unittest.mock import AsyncMock, MagicMock

from app.example import service
from app.example import view as example_view
from app.example.model import Item, ItemCreate
from main import app


async def test_list_items_endpoint(client, monkeypatch):
    fake_items = [Item(id=1, name="book", description="novel")]

    async def fake_get_items(_session):
        return fake_items

    async def override_get_db():
        yield object()

    monkeypatch.setattr(example_view.service, "get_items", fake_get_items)
    app.dependency_overrides[example_view.get_db] = override_get_db

    try:
        response = await client.get("/items/")
    finally:
        app.dependency_overrides.pop(example_view.get_db, None)

    assert response.status_code == 200
    assert response.json() == [{"id": 1, "name": "book", "description": "novel"}]


async def test_get_item_not_found_endpoint(client, monkeypatch):
    async def fake_get_item(_session, _item_id):
        return None

    async def override_get_db():
        yield object()

    monkeypatch.setattr(example_view.service, "get_item", fake_get_item)
    app.dependency_overrides[example_view.get_db] = override_get_db

    try:
        response = await client.get("/items/999")
    finally:
        app.dependency_overrides.pop(example_view.get_db, None)

    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}


async def test_create_item_endpoint(client, monkeypatch):
    created = Item(id=2, name="pen", description="blue")

    async def fake_create_item(_session, _payload):
        return created

    async def override_get_db():
        yield object()

    monkeypatch.setattr(example_view.service, "create_item", fake_create_item)
    app.dependency_overrides[example_view.get_db] = override_get_db

    try:
        response = await client.post("/items/", json={"name": "pen", "description": "blue"})
    finally:
        app.dependency_overrides.pop(example_view.get_db, None)

    assert response.status_code == 201
    assert response.json() == {"id": 2, "name": "pen", "description": "blue"}


async def test_service_get_items_returns_all():
    expected = [Item(id=1, name="book", description="novel")]

    class Result:
        def all(self):
            return expected

    session = AsyncMock()
    session.exec = AsyncMock(return_value=Result())

    result = await service.get_items(session)

    assert result == expected


async def test_service_get_item_by_id():
    expected = Item(id=5, name="chair", description=None)
    session = AsyncMock()
    session.get = AsyncMock(return_value=expected)

    result = await service.get_item(session, 5)

    assert result == expected


async def test_service_create_item_commits_and_refreshes():
    session = AsyncMock()
    session.add = MagicMock()
    payload = ItemCreate(name="lamp", description="desk")

    async def refresh_side_effect(item):
        item.id = 42

    session.refresh = AsyncMock(side_effect=refresh_side_effect)

    created = await service.create_item(session, payload)

    session.add.assert_called_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert created.id == 42
    assert created.name == "lamp"
    assert created.description == "desk"
