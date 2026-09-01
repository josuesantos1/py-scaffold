"""Application entry point."""

import importlib
import sys
import time
import uuid
from pathlib import Path

import structlog
from blacksheep import Application, Request, Response
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info
from structlog.contextvars import bind_contextvars, clear_contextvars

from config.database import close_pool, init_pool
from config.di import configure_services
from config.exceptions import AppException
from config.log import setup_logging
from config.metrics import REQUEST_COUNT, REQUEST_LATENCY
from config.nats import close_nats, connect_nats
from config.responses import error
from config.settings import settings

if sys.platform != "win32":
    try:
        import uvloop  # type: ignore[import-not-found]

        uvloop.install()
    except ImportError:
        pass

logger = structlog.get_logger()

_SKIP_METRICS: frozenset[str] = frozenset(
    ["/admin/health", "/admin/ready", "/admin/metrics"]
)

_app = Application(show_error_details=settings.debug)

docs = OpenAPIHandler(
    info=Info(
        title="My API",
        version="1.0.0",
    )
)

docs.bind_app(_app)


async def _startup(_application: Application) -> None:
    setup_logging()
    await init_pool()
    await connect_nats()
    logger.info("application_started", app=settings.app_name, version=settings.app_version)


async def _shutdown(_application: Application) -> None:
    await close_nats()
    await close_pool()
    logger.info("application_stopped")


_app.on_start += _startup
_app.on_stop += _shutdown

_app.use_cors(
    allow_origins=settings.cors_origins,
    allow_methods="*",
    allow_headers="*",
    allow_credentials=settings.cors_allow_credentials,
)


@_app.exception_handler(AppException)
async def _handle_app_exception(
    _self: Application, _req: Request, exc: AppException
) -> Response:
    return error(exc.message, exc.status_code)


@_app.exception_handler(Exception)
async def _handle_generic_exception(
    _self: Application, req: Request, exc: Exception
) -> Response:
    logger.error("unhandled_exception", exc_info=exc, path=str(req.url))
    return error("Internal server error", 500)


configure_services(_app)

for _view_path in sorted(Path("app").glob("*/view.py")):
    _app_name = _view_path.parent.name
    _module = importlib.import_module(f"app.{_app_name}.view")
    if hasattr(_module, "router") and hasattr(_module, "PREFIX"):
        for _method, _route in _module.router.registered_routes:
            _app.router.add(_method, _route.pattern, _route.handler)
        logger.debug("router.registered", app=_app_name, prefix=_module.PREFIX)


class _RequestIdMiddleware:
    __slots__ = ("_app",)

    def __init__(self, inner: object) -> None:
        self._app = inner

    async def __call__(self, scope: dict, receive: object, send: object) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self._app(scope, receive, send)  # type: ignore[misc]
            return

        headers: dict[bytes, bytes] = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        clear_contextvars()
        bind_contextvars(request_id=request_id)

        rid_bytes = request_id.encode()

        async def _send_with_id(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers_out = list(message.get("headers", []))
                headers_out.append((b"x-request-id", rid_bytes))
                message = {**message, "headers": headers_out}
            await send(message)  # type: ignore[misc]

        await self._app(scope, receive, _send_with_id)  # type: ignore[misc]


class _MetricsMiddleware:
    __slots__ = ("_app",)

    def __init__(self, inner: object) -> None:
        self._app = inner

    async def __call__(self, scope: dict, receive: object, send: object) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)  # type: ignore[misc]
            return

        path: str = scope.get("path", "")
        if path in _SKIP_METRICS:
            await self._app(scope, receive, send)  # type: ignore[misc]
            return

        start = time.monotonic()
        status_code = 500
        method: str = scope.get("method", "GET")

        async def _capture_status(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)  # type: ignore[misc]

        try:
            await self._app(scope, receive, _capture_status)  # type: ignore[misc]
        finally:
            latency = time.monotonic() - start
            REQUEST_COUNT.labels(method, path, str(status_code)).inc()
            REQUEST_LATENCY.labels(path).observe(latency)


app = _MetricsMiddleware(_RequestIdMiddleware(_app))
