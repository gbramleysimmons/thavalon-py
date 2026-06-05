"""Shared test helpers."""
from __future__ import annotations

import random
from typing import List, Optional

from app.domain.enums import RoleName
from app.domain.game import Game
from app.domain.role import Role
from app.domain.ruleset import make_custom_ruleset, standard_ruleset


def roll_standard(size: int, seed: int) -> Game:
    return standard_ruleset(size).make_game(
        [f"p{i}" for i in range(size)], random.Random(seed)
    )


def roll_custom(
    role_names: List[str], num_players: int, seed: int, duplicates: bool = False
) -> Game:
    ruleset = make_custom_ruleset(role_names, duplicates)
    return ruleset.make_game(
        [f"p{i}" for i in range(num_players)], random.Random(seed)
    )


def find(game: Game, name: RoleName) -> Optional[Role]:
    for role in game.roles:
        if role.role_name is name:
            return role
    return None


def players_of(roles: List[Role]) -> set:
    return {r.player for r in roles}


def seen_players(role: Role) -> set:
    return {info.seen.player for info in role.information.seen}
