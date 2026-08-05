"""Admin endpoints: health, readiness, metrics."""

from blacksheep import Response, Router
from blacksheep.contents import Content

from config.metrics import CONTENT_TYPE_LATEST, get_metrics_bytes
from config.responses import health_ok, ready_ok

PREFIX = "/admin"
TAGS = ["admin"]

router = Router(prefix=PREFIX)


@router.get("/health")
async def health() -> Response:
    return health_ok()


@router.get("/ready")
async def ready() -> Response:
    return ready_ok()


@router.get("/metrics")
async def metrics() -> Response:
    data = await get_metrics_bytes()
    return Response(200, content=Content(CONTENT_TYPE_LATEST.encode(), data))
