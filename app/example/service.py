"""Business logic for the example app."""

import asyncpg
import structlog

from app.example import repository
from app.example.model import Item, ItemCreate

logger = structlog.get_logger()


async def get_items(conn: asyncpg.Connection) -> list[Item]:  # type: ignore[type-arg]
    return await repository.fetch_items(conn)


async def get_item(conn: asyncpg.Connection, item_id: int) -> Item | None:  # type: ignore[type-arg]
    return await repository.fetch_item(conn, item_id)


async def create_item(conn: asyncpg.Connection, payload: ItemCreate) -> Item:  # type: ignore[type-arg]
    item = await repository.insert_item(conn, payload)
    logger.info("item_created", id=item.id, name=item.name)
    return item
