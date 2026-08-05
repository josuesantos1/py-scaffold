"""Dependency injection container."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg
from blacksheep import Application

import config.database as _database


class Database:
    @asynccontextmanager
    async def connection(self) -> AsyncIterator[asyncpg.Connection]:  # type: ignore[type-arg]
        async with _database.get_db() as conn:
            yield conn  # type: ignore[misc]


def configure_services(app: Application) -> None:
    app.services.add_transient(Database)
