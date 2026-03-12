"""Tests for teste app."""
from fastapi import APIRouter

from app.teste.view import router


def test_teste_placeholder() -> None:
    """Placeholder test."""
    assert True


def test_teste_router_is_available() -> None:
    """Ensure teste router object is created."""
    assert isinstance(router, APIRouter)
