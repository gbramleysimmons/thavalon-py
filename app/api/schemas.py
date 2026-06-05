"""Pydantic request/response models for the REST API."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class NamesRequest(BaseModel):
    """Body for ``POST /names`` to roll a new game."""

    names: List[str]
    custom: Optional[Dict[str, bool]] = None
    duplicates: Optional[bool] = False


class PlayerInfo(BaseModel):
    """A single player's view, as served by ``GET /game/info/{id}``."""

    name: str
    role: str
    description: str
    information: Dict[str, List[str]]
    allegiance: str


class GameOverRequest(BaseModel):
    """Body for ``POST /gameover/{id}``.

    ``result``/``record`` are accepted for compatibility; result persistence is
    not implemented (matching the original), so the game is simply cleared.
    """

    result: Optional[str] = None
    record: bool = True


class CurrentGamesRequest(BaseModel):
    numGames: int = Field(ge=0)
