"""Shared msgspec + BlackSheep response helpers."""

import msgspec
from blacksheep import Response
from blacksheep.contents import Content

_encoder = msgspec.json.Encoder()
_JSON = b"application/json"

_HEALTH_OK: bytes = _encoder.encode({"status": "healthy"})
_READY_OK: bytes = _encoder.encode({"status": "ready"})


def ok(obj: object) -> Response:
    return Response(200, content=Content(_JSON, _encoder.encode(obj)))


def created(obj: object) -> Response:
    return Response(201, content=Content(_JSON, _encoder.encode(obj)))


def not_found(message: str = "Not found") -> Response:
    return Response(404, content=Content(_JSON, _encoder.encode({"detail": message})))


def unprocessable(message: str) -> Response:
    return Response(422, content=Content(_JSON, _encoder.encode({"detail": message})))


def error(message: str, status: int = 500) -> Response:
    return Response(status, content=Content(_JSON, _encoder.encode({"detail": message})))


def health_ok() -> Response:
    return Response(200, content=Content(_JSON, _HEALTH_OK))


def ready_ok() -> Response:
    return Response(200, content=Content(_JSON, _READY_OK))
