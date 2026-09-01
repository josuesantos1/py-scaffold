"""Database access for the example app."""

import asyncpg
from opentelemetry import trace

from app.example.model import Item, ItemCreate

tracer = trace.get_tracer("app.example")


async def fetch_items(conn: asyncpg.Connection) -> list[Item]:  # type: ignore[type-arg]
    with tracer.start_as_current_span("db.get_items"):
        rows = await conn.fetch("SELECT id, name, description FROM items ORDER BY id")
    return [Item(id=r["id"], name=r["name"], description=r["description"]) for r in rows]


async def fetch_item(conn: asyncpg.Connection, item_id: int) -> Item | None:  # type: ignore[type-arg]
    with tracer.start_as_current_span("db.get_item") as span:
        span.set_attribute("item.id", item_id)
        row = await conn.fetchrow(
            "SELECT id, name, description FROM items WHERE id = $1",
            item_id,
        )
    if row is None:
        return None
    return Item(id=row["id"], name=row["name"], description=row["description"])


async def insert_item(conn: asyncpg.Connection, payload: ItemCreate) -> Item:  # type: ignore[type-arg]
    with tracer.start_as_current_span("db.create_item"):
        row = await conn.fetchrow(
            "INSERT INTO items (name, description) VALUES ($1, $2)"
            " RETURNING id, name, description",
            payload.name,
            payload.description,
        )
    return Item(id=row["id"], name=row["name"], description=row["description"])  # type: ignore[index]
