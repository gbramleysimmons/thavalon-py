"""Titania: a good role that plants false information on the evil team."""
from __future__ import annotations

from typing import List

from app.domain.enums import Alignment, RoleName, UpdaterPriority
from app.domain.game import Game
from app.domain.information import Alert, SingleSeen
from app.domain.role import Role, Updater


class Titania(Role):
    role_name = RoleName.TITANIA
    alignment = Alignment.GOOD

    _untargetable = (RoleName.COLGREVANCE,)

    def updaters(self, game: Game) -> List[Updater]:
        return [
            (self._oberon_present_alert, UpdaterPriority.TEN),
            (self._plant_false_info, UpdaterPriority.ONE),
        ]

    def _oberon_present_alert(self, game: Game) -> None:
        if any(r.role_name is RoleName.OBERON for r in game.evil_roles()):
            self.information.add(Alert("There is an Oberon in the game!"))

    def _plant_false_info(self, game: Game) -> None:
        targets = [r for r in game.evil_roles() if r.role_name not in self._untargetable]
        if not targets:
            return
        target = game.rng.choice(targets)
        target.information.add(SingleSeen(game.rng.choice(game.good_roles())))
        target.information.add(Alert("You have been Titania'd!"))
        self.information.add(
            Alert(
                "You have added false information to a player with the role of "
                + target.role_name.value
            )
        )
