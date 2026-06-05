"""Shared API dependencies."""
from __future__ import annotations

from app.store.registry import GameRegistry

_registry = GameRegistry()


def get_registry() -> GameRegistry:
    """Return the process-wide in-memory game registry."""
    return _registry
