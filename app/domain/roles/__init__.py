"""Role registry: maps role names to factories used when building rulesets.

This replaces the original implementation's reflection-based role lookup. Keys
are the role *class names* the API receives (including the ``Lone`` variants),
matching what the original frontend sent after its translations.
"""
from __future__ import annotations

from typing import Callable, Dict

from app.domain.role import Role
from app.domain.roles.evil import Agravaine, Colgrevance, Maelegant, Mordred, Morgana
from app.domain.roles.good import (
    Arthur,
    Galahad,
    Gawain,
    Guinevere,
    Lancelot,
    LonePercival,
    Merlin,
    Nimue,
    Percival,
)
from app.domain.roles.lovers import Iseult, LoneIseult, LoneTristan, Tristan
from app.domain.roles.oberon import Oberon
from app.domain.roles.titania import Titania

RoleFactory = Callable[[], Role]

ROLE_REGISTRY: Dict[str, RoleFactory] = {
    "Merlin": Merlin,
    "Percival": Percival,
    "LonePercival": LonePercival,
    "Guinevere": Guinevere,
    "Tristan": Tristan,
    "Iseult": Iseult,
    "LoneTristan": LoneTristan,
    "LoneIseult": LoneIseult,
    "Arthur": Arthur,
    "Galahad": Galahad,
    "Titania": Titania,
    "Nimue": Nimue,
    "Gawain": Gawain,
    "Lancelot": Lancelot,
    "Mordred": Mordred,
    "Morgana": Morgana,
    "Maelegant": Maelegant,
    "Oberon": Oberon,
    "Agravaine": Agravaine,
    "Colgrevance": Colgrevance,
}

__all__ = ["ROLE_REGISTRY", "RoleFactory"]
