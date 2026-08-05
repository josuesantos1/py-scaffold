"""AsyncPG connection pool."""

from contextlib import asynccontextmanager

import asyncpg

from config.settings import settings

_pool: asyncpg.Pool | None = None  # type: ignore[type-arg]

_DSN = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")


async def init_pool(**kwargs: object) -> None:  # type: ignore[misc]
    global _pool
    _pool = await asyncpg.create_pool(  # type: ignore[assignment]
        dsn=_DSN,
        min_size=5,
        max_size=20,
        max_queries=50_000,
        max_inactive_connection_lifetime=300.0,
        statement_cache_size=1024,
        command_timeout=30.0,
        **kwargs,  # type: ignore[arg-type]
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_db():  # type: ignore[return]
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Call await config.database.init_pool() during application startup."
        )
    async with _pool.acquire() as conn:
        yield conn
