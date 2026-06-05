"""Rulesets and the roll algorithm.

A ruleset knows which good and evil role *factories* are available and how to
draw a hand of roles. ``make_game`` repeatedly draws and validates until it
produces a legal game (or gives up after a bounded number of attempts).
"""
from __future__ import annotations

import random
from typing import List, Optional

from app.domain.enums import Alignment
from app.domain.game import Game, get_ratio
from app.domain.role import Role
from app.domain.roles import ROLE_REGISTRY, RoleFactory
from app.domain.roles.evil import Agravaine, Colgrevance, Maelegant, Mordred, Morgana
from app.domain.roles.good import (
    Arthur,
    Guinevere,
    Lancelot,
    Merlin,
    Percival,
)
from app.domain.roles.lovers import Iseult, Tristan
from app.domain.roles.oberon import Oberon
from app.domain.roles.titania import Titania

NUM_REROLLS = 100

#: Human-readable custom keys that expand to one or more canonical role names.
_CUSTOM_ALIASES = {
    "Lovers": ["Tristan", "Iseult"],
    "Lone Lovers": ["LoneTristan", "LoneIseult"],
    "Lone Percival": ["LonePercival"],
}
_DUPLICATE_KEY = "Duplicate Roles"


class RollError(ValueError):
    """Raised when a valid game cannot be produced from the requested config."""


class Ruleset:
    """Draws roles without replacement (no duplicate roles)."""

    def __init__(self, good_roles: List[RoleFactory], evil_roles: List[RoleFactory]) -> None:
        self.good_roles = good_roles
        self.evil_roles = evil_roles

    def draw_roles(
        self, choices: List[RoleFactory], num: int, rng: random.Random
    ) -> List[Role]:
        if num > len(choices):
            raise RollError("Not enough roles")
        return [factory() for factory in rng.sample(choices, num)]

    def make_game(self, players: List[str], rng: Optional[random.Random] = None) -> Game:
        rng = rng or random.Random()
        ratio = get_ratio(len(players))
        if ratio is None:
            raise RollError(
                "Invalid number of players! Only games of 5, 7, 8, and 10 players "
                "are currently supported"
            )
        num_good, num_evil = ratio

        for _ in range(NUM_REROLLS + 1):
            roles = self.draw_roles(self.good_roles, num_good, rng)
            roles += self.draw_roles(self.evil_roles, num_evil, rng)
            rng.shuffle(roles)
            game = Game(roles, players, rng=rng)
            if game.set_up():
                return game
        raise RollError("Couldn't set up game")


class DuplicateRolesRuleset(Ruleset):
    """Draws roles with replacement, allowing duplicate roles."""

    def draw_roles(
        self, choices: List[RoleFactory], num: int, rng: random.Random
    ) -> List[Role]:
        return [rng.choice(choices)() for _ in range(num)]


# --- Standard rulesets -------------------------------------------------------

_STANDARD_EVIL: List[RoleFactory] = [Mordred, Morgana, Maelegant, Oberon]
_STANDARD_GOOD: List[RoleFactory] = [Merlin, Percival, Guinevere, Tristan, Iseult, Lancelot]
_EXTENDED_GOOD: List[RoleFactory] = _STANDARD_GOOD + [Titania, Arthur]


def standard_ruleset(num_players: int) -> Ruleset:
    """Return the default ruleset for a supported player count."""
    if num_players == 5:
        return Ruleset(_STANDARD_GOOD, _STANDARD_EVIL)
    if num_players == 7:
        return Ruleset(_EXTENDED_GOOD, _STANDARD_EVIL)
    if num_players == 8:
        return Ruleset(_EXTENDED_GOOD, _STANDARD_EVIL + [Agravaine])
    if num_players == 10:
        return Ruleset(_EXTENDED_GOOD, _STANDARD_EVIL + [Agravaine, Colgrevance])
    raise RollError(
        "Invalid number of players! Only games of 5, 7, 8, and 10 players are "
        "currently supported"
    )


def make_custom_ruleset(role_names: List[str], duplicates: bool) -> Ruleset:
    """Build a ruleset from a list of requested role names.

    Expands human-readable aliases (Lovers, Lone Lovers, Lone Percival) and the
    ``Duplicate Roles`` key, then partitions roles into good and evil.
    """
    expanded: List[str] = []
    for name in role_names:
        if name == _DUPLICATE_KEY:
            duplicates = True
            continue
        expanded.extend(_CUSTOM_ALIASES.get(name, [name]))

    good: List[RoleFactory] = []
    evil: List[RoleFactory] = []
    for name in expanded:
        factory = ROLE_REGISTRY.get(name)
        if factory is None:
            raise RollError(f"Unknown role: {name}")
        if factory().alignment is Alignment.GOOD:
            good.append(factory)
        else:
            evil.append(factory)

    if not good or not evil:
        raise RollError("not enough good or evil roles")

    return DuplicateRolesRuleset(good, evil) if duplicates else Ruleset(good, evil)
