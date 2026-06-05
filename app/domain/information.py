"""Information types and the per-role information aggregator.

Each piece of information references the :class:`~app.domain.role.Role` it is
about. Rendering to display strings is deferred to :meth:`Information.display`
so that roles can add their own flavour text in ``prepare_information``.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.domain.role import Role


class Information:
    """Base class for all information a role may hold."""

    def display(self) -> str:  # pragma: no cover - overridden by subclasses
        raise NotImplementedError


@dataclass
class Alert(Information):
    """Free-text information, e.g. "You have been Oberon'd!"."""

    text: str

    def display(self) -> str:
        return self.text


@dataclass
class RolePresent(Information):
    """Tells a player that a given role is present in the game."""

    present: Role

    def display(self) -> str:
        return f"{self.present.role_name.value} is in the game!"


@dataclass
class SingleSeen(Information):
    """Represents seeing a single player."""

    seen: Role

    def display(self) -> str:
        return self.seen.player


@dataclass
class PairSeen(Information):
    """Represents a relationship between two roles (Guinevere/Gawain).

    ``a`` and ``b`` are mutable because Oberon may replace one side with the
    Unknown role to corrupt the information.
    """

    a: Role
    b: Role

    def display(self) -> str:
        return f"{self.a.player}/{self.b.player}"


@dataclass
class Perfect(Information):
    """Perfect knowledge of a player and their role (Colgrevance)."""

    seen: Role

    def display(self) -> str:
        return f"{self.seen.player} is {self.seen.role_name.value}"


@dataclass
class InformationAggregator:
    """Holds and organises the information owned by a single role."""

    alerts: List[Alert] = field(default_factory=list)
    role_present: List[RolePresent] = field(default_factory=list)
    seen: List[SingleSeen] = field(default_factory=list)
    pair_seen: List[PairSeen] = field(default_factory=list)
    perfect: List[Perfect] = field(default_factory=list)

    def add(self, info: Information) -> None:
        if isinstance(info, Alert):
            self.alerts.append(info)
        elif isinstance(info, RolePresent):
            self.role_present.append(info)
        elif isinstance(info, SingleSeen):
            self.seen.append(info)
        elif isinstance(info, PairSeen):
            self.pair_seen.append(info)
        elif isinstance(info, Perfect):
            self.perfect.append(info)
        else:  # pragma: no cover - defensive
            raise TypeError(f"Unknown information type: {type(info)!r}")

    def add_all(self, infos) -> None:
        for info in infos:
            self.add(info)

    def shuffle(self, rng: random.Random) -> None:
        """Shuffle every bucket except alerts to remove ordering bias."""
        rng.shuffle(self.role_present)
        rng.shuffle(self.seen)
        rng.shuffle(self.pair_seen)
        rng.shuffle(self.perfect)
