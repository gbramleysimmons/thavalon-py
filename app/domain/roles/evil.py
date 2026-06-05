"""Evil roles whose only information is the rest of the evil team."""
from __future__ import annotations

from typing import List

from app.domain.enums import Alignment, Card, RoleName, UpdaterPriority
from app.domain.game import Game
from app.domain.information import Perfect
from app.domain.role import DefaultEvilRole, Role, Updater


class Mordred(DefaultEvilRole):
    role_name = RoleName.MORDRED


class Morgana(DefaultEvilRole):
    role_name = RoleName.MORGANA


class Maelegant(DefaultEvilRole):
    role_name = RoleName.MAELEGANT

    def description(self) -> str:
        return (
            super().description()
            + "\nAbility: Reversal\nYou can play reverses on missions. A reverse"
            " inverts the result of a mission: A successful mission will fail and"
            " a failing mission will succeed."
        )

    def card_options(self) -> List[Card]:
        return [Card.PASS, Card.FAIL, Card.REVERSE]


class Agravaine(DefaultEvilRole):
    role_name = RoleName.AGRAVAINE

    def card_options(self) -> List[Card]:
        return [Card.FAIL]


class Colgrevance(Role):
    """Knows every other evil player perfectly, but is hidden from them.

    Colgrevance deliberately does *not* extend :class:`DefaultEvilRole`; the
    default evil "sees evil team" updater excludes Colgrevance, so the rest of
    evil never sees Colgrevance.
    """

    role_name = RoleName.COLGREVANCE
    alignment = Alignment.EVIL

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        for role in game.evil_roles():
            if role is not self:
                self.information.add(Perfect(role))
