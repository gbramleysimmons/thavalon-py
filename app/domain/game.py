"""The :class:`Game`: validation, information assembly and player assignment."""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from app.domain.enums import Alignment, RoleName, UpdaterPriority
from app.domain.information import Alert
from app.domain.role import Role, Updater

#: Supported player counts mapped to (good, evil) team sizes.
_RATIOS = {5: (3, 2), 7: (4, 3), 8: (5, 3), 10: (6, 4)}

#: Evil roles that can never receive Hijack.
_HIJACK_EXCLUDED = (RoleName.MORDRED, RoleName.COLGREVANCE)


class Game:
    """A rolled game: a fixed set of roles assigned to a set of players."""

    def __init__(
        self,
        roles: List[Role],
        players: List[str],
        rng: Optional[random.Random] = None,
    ) -> None:
        self.rng = rng or random.Random()
        self.roles: List[Role] = list(roles)
        self.players: List[str] = list(players)
        # Shuffling the players randomises which player starts the game.
        self.rng.shuffle(self.players)

    def good_roles(self) -> List[Role]:
        return [r for r in self.roles if r.alignment is Alignment.GOOD]

    def evil_roles(self) -> List[Role]:
        return [r for r in self.roles if r.alignment is Alignment.EVIL]

    def _ratio_ok(self) -> bool:
        ratio = _RATIOS.get(len(self.roles))
        if ratio is None:
            return False
        good, evil = ratio
        return len(self.good_roles()) == good and len(self.evil_roles()) == evil

    def _validate(self) -> bool:
        return self._ratio_ok() and all(r.game_ok(self) for r in self.roles)

    def _fill_information(self) -> None:
        updaters: List[Updater] = []
        for role in self.roles:
            updaters.extend(role.updaters(self))
        updaters.append((self._hijack_updater, UpdaterPriority.ONE))

        # Apply in descending priority so base info exists before it is read or
        # corrupted by lower-priority updaters.
        for func, _priority in sorted(updaters, key=lambda u: u[1].value, reverse=True):
            func(self)

        # Shuffle each role's information to remove ordering bias.
        for role in self.roles:
            role.information.shuffle(self.rng)

    def _hijack_updater(self, game: Game) -> None:
        if len(self.roles) <= 5:
            return  # No hijack in 5-player games.
        candidates = [r for r in self.evil_roles() if r.role_name not in _HIJACK_EXCLUDED]
        if candidates:
            self.rng.choice(candidates).information.add(Alert("You have Hijack!"))

    def _assign_players(self) -> None:
        assert len(self.roles) == len(self.players)
        for role, name in zip(self.roles, self.players):
            role.player = name

    def set_up(self) -> bool:
        """Validate, compute information and assign players.

        Returns ``False`` if the rolled configuration is invalid.
        """
        if not self._validate():
            return False
        self._fill_information()
        self._assign_players()
        return True


def get_ratio(num_players: int) -> Optional[Tuple[int, int]]:
    """Return the (good, evil) split for a player count, or ``None`` if unsupported."""
    return _RATIOS.get(num_players)
