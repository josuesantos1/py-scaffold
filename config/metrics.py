"""Prometheus metrics.

Multiprocess mode:
- When PROMETHEUS_MULTIPROC_DIR is set (required for Granian --workers N),
  generate_latest() collects from all worker mmap files via MultiProcessCollector.
- generate_latest() is synchronous and O(n*m) in metric cardinality; always
  run it off the event loop via asyncio.to_thread().
"""

import asyncio
import os

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
    multiprocess,
)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"],
)


def _make_registry() -> CollectorRegistry | None:
    """Return a MultiProcessCollector registry when multiprocess dir is set."""
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    return None


async def get_metrics_bytes() -> bytes:
    """Collect metrics off the event loop and return Prometheus text format."""
    registry = _make_registry()
    if registry is None:
        return await asyncio.to_thread(generate_latest)
    return await asyncio.to_thread(generate_latest, registry)


__all__ = [
    "CONTENT_TYPE_LATEST",
    "REQUEST_COUNT",
    "REQUEST_LATENCY",
    "get_metrics_bytes",
]
