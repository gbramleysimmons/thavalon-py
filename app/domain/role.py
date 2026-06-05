"""The :class:`Role` base class and shared evil-role behaviour.

A role owns an :class:`InformationAggregator` and contributes zero or more
*updaters*: ``(callable, priority)`` pairs that mutate the game's information.
Updaters run in descending priority order (see :class:`UpdaterPriority`).

Note: ``card_options`` is part of the domain model but is **not** serialized by
the REST API (the original ``jsonifyGame`` emits only name/role/description/
information/allegiance). It is kept here to document each role's intent.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

from app.domain.enums import Alignment, Card, RoleName, UpdaterPriority
from app.domain.information import InformationAggregator, SingleSeen

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.domain.game import Game

Updater = Tuple[Callable[["Game"], None], UpdaterPriority]


class Role:
    """Base class for every role in the game."""

    #: The role's identity. Subclasses override this.
    role_name: RoleName = RoleName.UNKNOWN
    alignment: Alignment = Alignment.UNKNOWN

    def __init__(self) -> None:
        self.player: str = "????"
        self.information = InformationAggregator()

    def description(self) -> str:
        if self.alignment is Alignment.EVIL:
            return "You are a member of the Evil council"
        if self.alignment is Alignment.GOOD:
            return "You are on the good team"
        return "Unknown Role"

    def card_options(self) -> List[Card]:
        return [Card.PASS]

    def game_ok(self, game: Game) -> bool:
        """Whether this role is content with the rest of the rolled game."""
        return True

    def updaters(self, game: Game) -> List[Updater]:
        return []

    def prepare_information(self) -> Dict[str, List[str]]:
        """Render this role's information into display strings.

        Subclasses override to add flavour text to individual buckets.
        """
        info = self.information
        return {
            "alerts": [i.display() for i in info.alerts],
            "rolePresent": [i.display() for i in info.role_present],
            "seen": [i.display() for i in info.seen],
            "pairSeen": [i.display() for i in info.pair_seen],
            "perfect": [i.display() for i in info.perfect],
        }


class DefaultEvilRole(Role):
    """Evil role whose only base information is the rest of the evil team.

    Colgrevance is excluded from what every evil role sees, which is what keeps
    Colgrevance hidden from the rest of evil.
    """

    alignment = Alignment.EVIL

    def card_options(self) -> List[Card]:
        return [Card.PASS, Card.FAIL]

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._sees_evil_team, UpdaterPriority.TEN)]

    def _sees_evil_team(self, game: Game) -> None:
        for role in game.evil_roles():
            if role is self or role.role_name is RoleName.COLGREVANCE:
                continue
            self.information.add(SingleSeen(role))

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        m["seen"] = [f"{s} is a fellow member of the Evil council" for s in m["seen"]]
        return m


class UnknownRole(Role):
    """Placeholder role used by Oberon to corrupt another player's information."""

    role_name = RoleName.UNKNOWN
    alignment = Alignment.UNKNOWN


#: Shared singleton, mirroring the original ``object UnknownRole``.
UNKNOWN_ROLE = UnknownRole()
