"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from app.api.dependencies import get_registry


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure each test starts with an empty game registry."""
    registry = get_registry()
    registry._games.clear()
    yield
    registry._games.clear()
