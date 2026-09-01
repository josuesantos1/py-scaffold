"""HTTP handlers for the example app.

Pattern:
- Declare ``db: Database`` parameter — BlackSheep injects it per request.
- Call ``async with db.connection() as conn:`` to acquire a DB connection.
- Use the module-level msgspec codec (item_decoder) — no per-request
  allocations.
- Return explicit Response objects with pre-encoded bytes for full control
  over serialisation.
"""

import structlog
from blacksheep import Request, Response, Router

from app.example import service
from app.example.model import ItemCreate, item_decoder
from config.di import Database
from config.responses import created, not_found, ok, unprocessable

PREFIX = "/v1/items"
TAGS = ["items"]

logger = structlog.get_logger()

router = Router(prefix=PREFIX)


@router.get("/")
async def list_items(db: Database) -> Response:
    async with db.connection() as conn:
        items = await service.get_items(conn)  # type: ignore[arg-type]
    return ok(items)


@router.get("/{item_id}")
async def get_item(item_id: int, db: Database) -> Response:
    async with db.connection() as conn:
        item = await service.get_item(conn, item_id)  # type: ignore[arg-type]
    if item is None:
        logger.warning("item_not_found", item_id=item_id)
        return not_found("Item not found")
    return ok(item)


@router.post("/")
async def create_item(request: Request, db: Database) -> Response:
    body = (await request.read()) or b""
    try:
        payload = item_decoder.decode(body)
    except Exception as exc:
        return unprocessable(str(exc))
    async with db.connection() as conn:
        item = await service.create_item(conn, payload)  # type: ignore[arg-type]
    return created(item)


__all__ = ["router", "service", "ItemCreate"]
