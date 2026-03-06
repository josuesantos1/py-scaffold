import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.admin.view import router as admin_router
from app.example.view import router as example_router
from config.database import engine
from config.exceptions import AppException, app_exception_handler, generic_exception_handler
from config.log import setup_logging
from config.metrics import REQUEST_COUNT, REQUEST_LATENCY
from config.settings import settings

_SKIP_METRICS = {"/admin/health", "/admin/ready", "/admin/metrics"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path in _SKIP_METRICS:
        return await call_next(request)

    start = time.time()
    response = await call_next(request)
    latency = time.time() - start

    REQUEST_COUNT.labels(
        request.method,
        request.url.path,
        response.status_code,
    ).inc()

    REQUEST_LATENCY.labels(request.url.path).observe(latency)

    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    clear_contextvars()
    bind_contextvars(request_id=str(uuid.uuid4()))
    return await call_next(request)


app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(example_router, prefix="/items", tags=["items"])
