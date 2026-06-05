"""In-memory registry of rolled games.

Mirrors the original ``staticGames`` map: games live only in memory and are
removed when the game ends. All mutations are guarded by a lock so that a game
is recorded/removed at most once even under concurrent requests.
"""
from __future__ import annotations

import threading
import uuid
from typing import Dict, List, Optional

from app.domain.game import Game

ID_LENGTH = 4


class GameRegistry:
    def __init__(self) -> None:
        self._games: Dict[str, Game] = {}
        self._lock = threading.Lock()

    def _new_id(self) -> str:
        while True:
            game_id = uuid.uuid4().hex[:ID_LENGTH]
            if game_id not in self._games:
                return game_id

    def add(self, game: Game) -> str:
        with self._lock:
            game_id = self._new_id()
            self._games[game_id] = game
            return game_id

    def get(self, game_id: str) -> Optional[Game]:
        return self._games.get(game_id)

    def exists(self, game_id: str) -> bool:
        return game_id in self._games

    def remove(self, game_id: str) -> bool:
        """Remove a game; return ``True`` if it existed (i.e. result recorded)."""
        with self._lock:
            return self._games.pop(game_id, None) is not None

    def recent_ids(self, num_games: int) -> List[str]:
        """Return up to ``num_games`` ids, newest first."""
        if num_games <= 0:
            return []
        ids = list(self._games.keys())
        return ids[-num_games:][::-1]
