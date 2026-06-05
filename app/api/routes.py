"""REST API routes — a role dealer and information service for in-person play."""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends

from app.api.dependencies import get_registry
from app.api.schemas import CurrentGamesRequest, GameOverRequest, NamesRequest, PlayerInfo
from app.domain.game import Game
from app.domain.ruleset import RollError, make_custom_ruleset, standard_ruleset
from app.store.registry import GameRegistry

router = APIRouter()


def _serialize_game(game: Game) -> List[PlayerInfo]:
    return [
        PlayerInfo(
            name=role.player,
            role=role.role_name.value,
            description=role.description(),
            information=role.prepare_information(),
            allegiance=role.alignment.value,
        )
        for role in game.roles
    ]


def _roll_game(req: NamesRequest) -> Game:
    if req.custom is not None:
        requested = [name for name, enabled in req.custom.items() if enabled]
        ruleset = make_custom_ruleset(requested, bool(req.duplicates))
    else:
        ruleset = standard_ruleset(len(req.names))
    return ruleset.make_game(list(req.names))


@router.get("/health")
def health() -> str:
    return "Thavalon API"


@router.post("/names")
def create_game(
    req: NamesRequest, registry: GameRegistry = Depends(get_registry)
) -> Dict[str, str]:
    try:
        game = _roll_game(req)
    except RollError as exc:
        return {"error": str(exc)}
    game_id = registry.add(game)
    return {"id": game_id}


@router.get("/game/info/{game_id}")
def game_info(
    game_id: str, registry: GameRegistry = Depends(get_registry)
) -> List[PlayerInfo]:
    game = registry.get(game_id)
    if game is None:
        return []
    return _serialize_game(game)


@router.get("/isGame/{game_id}")
def is_game(game_id: str, registry: GameRegistry = Depends(get_registry)) -> bool:
    return registry.exists(game_id)


@router.post("/gameover/{game_id}")
def game_over(
    game_id: str,
    payload: Optional[GameOverRequest] = None,
    registry: GameRegistry = Depends(get_registry),
) -> bool:
    # Result persistence is intentionally not implemented; ending a game simply
    # removes it. Returns True if the game still existed (i.e. was recorded now).
    return registry.remove(game_id)


@router.post("/currentgames")
def current_games(
    req: CurrentGamesRequest, registry: GameRegistry = Depends(get_registry)
) -> List[str]:
    return registry.recent_ids(req.numGames)
