"""Structured logging configuration.

HPC optimisations applied:
- cache_logger_on_first_use=True  — eliminates factory lookup on every call
- orjson.dumps as JSONRenderer serializer — 5-10x faster than stdlib json
- Minimal processor chain (no unused processors)
- UTC timestamps for consistency across multi-region deployments
"""

import logging

import orjson
import structlog
from structlog.contextvars import merge_contextvars

from config.settings import settings


def _orjson_dumps(obj: object, **_: object) -> str:
    """orjson serializer wrapper — returns str for structlog compatibility."""
    return orjson.dumps(obj).decode("utf-8")


def setup_logging() -> None:
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(format="%(message)s", level=log_level)

    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(serializer=_orjson_dumps),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
