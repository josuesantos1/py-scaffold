"""Integration tests: real queries against an in-memory SQLite database."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.example import service
from app.example import view as example_view
from app.example.model import ItemCreate
from config.database import get_db

_SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    engine = create_async_engine(_SQLITE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def integration_client(db_session: AsyncSession):
    mini_app = FastAPI()
    mini_app.include_router(example_view.router, prefix="/items")

    async def override_get_db():
        yield db_session

    mini_app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=mini_app), base_url="http://test") as ac:
        yield ac


async def test_create_and_list_items_against_sqlite(integration_client: AsyncClient):
    create_response = await integration_client.post(
        "/items/", json={"name": "sword", "description": "sharp"}
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "sword"
    assert created["id"] is not None

    list_response = await integration_client.get("/items/")
    assert list_response.status_code == 200
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["name"] == "sword"


async def test_get_item_by_id_against_sqlite(integration_client: AsyncClient):
    create_response = await integration_client.post("/items/", json={"name": "shield"})
    item_id = create_response.json()["id"]

    get_response = await integration_client.get(f"/items/{item_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "shield"


async def test_get_missing_item_returns_404(integration_client: AsyncClient):
    response = await integration_client.get("/items/9999")
    assert response.status_code == 404


async def test_service_create_item_persists(db_session: AsyncSession):
    payload = ItemCreate(name="axe", description="heavy")
    item = await service.create_item(db_session, payload)

    assert item.id is not None
    fetched = await service.get_item(db_session, item.id)
    assert fetched is not None
    assert fetched.name == "axe"
