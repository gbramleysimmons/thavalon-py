"""The Lovers: Tristan and Iseult (and their Lone variants)."""
from __future__ import annotations

from typing import Dict, List

from app.domain.enums import Alignment, RoleName, UpdaterPriority
from app.domain.game import Game
from app.domain.information import Alert, SingleSeen
from app.domain.role import Role, Updater


class _Lover(Role):
    """Shared Lover behaviour. A lover sees every instance of their partner role."""

    alignment = Alignment.GOOD

    def _other_lover(self) -> RoleName:
        return RoleName.ISEULT if self.role_name is RoleName.TRISTAN else RoleName.TRISTAN

    def _adjective(self) -> str:
        return "luxurious" if self._other_lover() is RoleName.TRISTAN else "luscious"

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        partners = [r for r in game.good_roles() if r.role_name is self._other_lover()]
        if not partners:
            self.information.add(Alert("You are a sad and lonely lover"))
            return
        for partner in partners:
            self.information.add(SingleSeen(partner))

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        adjective = self._adjective()
        partner = self._other_lover().value
        m["seen"] = [f"You see {s} as your {adjective} lover {partner}" for s in m["seen"]]
        return m


class _NonLoneLover(_Lover):
    """Lover that vetoes a game where their partner is absent."""

    def game_ok(self, game: Game) -> bool:
        return any(r.role_name is self._other_lover() for r in game.good_roles())


class Tristan(_NonLoneLover):
    role_name = RoleName.TRISTAN


class Iseult(_NonLoneLover):
    role_name = RoleName.ISEULT


class LoneTristan(_Lover):
    role_name = RoleName.TRISTAN


class LoneIseult(_Lover):
    role_name = RoleName.ISEULT
