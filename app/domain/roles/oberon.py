"""Oberon: an evil role that corrupts one good player's information."""
from __future__ import annotations

from typing import List, Optional

from app.domain.enums import RoleName, UpdaterPriority
from app.domain.game import Game
from app.domain.information import Alert, RolePresent, SingleSeen
from app.domain.role import UNKNOWN_ROLE, DefaultEvilRole, Role, Updater

_SINGLE_SEEN_TARGETS = (RoleName.TRISTAN, RoleName.ISEULT, RoleName.PERCIVAL, RoleName.MERLIN)
_PAIR_SEEN_TARGETS = (RoleName.GUINEVERE, RoleName.GAWAIN)
_ROLE_PRESENT_TARGETS = (RoleName.ARTHUR, RoleName.NIMUE)
_ALL_TARGETS = _SINGLE_SEEN_TARGETS + _PAIR_SEEN_TARGETS + _ROLE_PRESENT_TARGETS


class Oberon(DefaultEvilRole):
    role_name = RoleName.OBERON

    def updaters(self, game: Game) -> List[Updater]:
        # Runs last (priority ONE) so it corrupts already-computed information.
        return super().updaters(game) + [(self._corrupt, UpdaterPriority.ONE)]

    def _pick_target(self, game: Game) -> Optional[Role]:
        candidates = [r for r in game.good_roles() if r.role_name in _ALL_TARGETS]
        if not candidates:
            return None
        return game.rng.choice(candidates)

    def _corrupt(self, game: Game) -> None:
        target = self._pick_target(game)
        if target is None:
            return

        if target.role_name in _SINGLE_SEEN_TARGETS:
            self._corrupt_single_seen(game, target)
        elif target.role_name in _PAIR_SEEN_TARGETS:
            if not target.information.pair_seen:
                return  # nothing to corrupt; no alerts are issued
            self._corrupt_pair_seen(game, target)
        elif target.role_name in _ROLE_PRESENT_TARGETS:
            self._corrupt_role_present(game, target)

        target.information.add(Alert("You have been Oberon'd!"))
        self.information.add(Alert("You have added false information to a member of the good team"))

    def _corrupt_single_seen(self, game: Game, target: Role) -> None:
        already_seen = {target}
        already_seen.update(info.seen for info in target.information.seen)
        candidates = [r for r in game.roles if r not in already_seen]
        if not candidates:
            return
        target.information.add(SingleSeen(game.rng.choice(candidates)))

    def _corrupt_pair_seen(self, game: Game, target: Role) -> None:
        info = game.rng.choice(target.information.pair_seen)
        if game.rng.random() < 0.5:
            info.a = UNKNOWN_ROLE
        else:
            info.b = UNKNOWN_ROLE

    def _corrupt_role_present(self, game: Game, target: Role) -> None:
        present = target.information.role_present
        present.remove(game.rng.choice(present))
        present.append(RolePresent(UNKNOWN_ROLE))
