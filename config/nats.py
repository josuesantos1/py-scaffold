"""NATS JetStream connection management."""

from collections.abc import Awaitable, Callable

import nats
import structlog
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

from config.settings import settings

logger = structlog.get_logger()

_nc: Client | None = None


async def connect() -> Client:
    """Return a connected NATS client, connecting on first use."""
    global _nc
    if _nc is None or _nc.is_closed:
        _nc = await nats.connect(settings.nats_url)
        logger.info("nats.connected", url=settings.nats_url)
    return _nc


async def setup_streams(nc: Client) -> JetStreamContext:
    """Return the JetStream context used for stream/consumer management."""
    return nc.jetstream()


async def connect_nats() -> None:
    """Connect to NATS during application startup."""
    await connect()


async def close_nats() -> None:
    """Drain and close the NATS connection during application shutdown."""
    global _nc
    if _nc is not None:
        await _nc.drain()
        _nc = None
        logger.info("nats.closed")


async def subscribe_wildcard(
    handler: Callable[[Msg], Awaitable[None]], subject: str = ">"
) -> None:
    """Subscribe ``handler`` to all subjects (or a given wildcard subject)."""
    nc = await connect()
    await nc.subscribe(subject, cb=handler)
