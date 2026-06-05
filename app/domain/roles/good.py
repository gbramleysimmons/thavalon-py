"""Good-aligned roles whose behaviour is self-contained."""
from __future__ import annotations

from typing import Dict, List

from app.domain.enums import Alignment, Card, RoleName, UpdaterPriority
from app.domain.game import Game
from app.domain.information import Alert, PairSeen, RolePresent, SingleSeen
from app.domain.role import Role, Updater


class Merlin(Role):
    role_name = RoleName.MERLIN
    alignment = Alignment.GOOD

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        # Merlin sees all evil except Mordred, plus any Lancelot (who looks evil).
        for role in game.evil_roles():
            if role.role_name is not RoleName.MORDRED:
                self.information.add(SingleSeen(role))
        for role in game.good_roles():
            if role.role_name is RoleName.LANCELOT:
                self.information.add(SingleSeen(role))

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        m["seen"] = [f"You see {s} as Evil (Or Lancelot)" for s in m["seen"]]
        return m


class LonePercival(Role):
    """Percival who is content even if there is no Merlin/Morgana to see."""

    role_name = RoleName.PERCIVAL
    alignment = Alignment.GOOD

    _targets = (RoleName.MERLIN, RoleName.MORGANA)

    def _sees(self, role: Role) -> bool:
        return role.role_name in self._targets

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        for role in game.roles:
            if self._sees(role):
                self.information.add(SingleSeen(role))

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        m["seen"] = [f"You see {s} as Merlin (Or Morgana)" for s in m["seen"]]
        return m


class Percival(LonePercival):
    """Standard Percival: vetoes a game where there is nobody to see."""

    def game_ok(self, game: Game) -> bool:
        return any(self._sees(role) for role in game.roles)


class Lancelot(Role):
    role_name = RoleName.LANCELOT
    alignment = Alignment.GOOD

    def description(self) -> str:
        return (
            super().description()
            + "\nAbility: Reversal\nYou can play reverses on missions. A reverse"
            " inverts the result of a mission: A successful mission will fail and"
            " a failing mission will succeed."
        )

    def card_options(self) -> List[Card]:
        return [Card.PASS, Card.REVERSE]


class Galahad(Role):
    """Plain Good role; the night-phase/declaration version was never implemented."""

    role_name = RoleName.GALAHAD
    alignment = Alignment.GOOD


class Arthur(Role):
    role_name = RoleName.ARTHUR
    alignment = Alignment.GOOD

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        for role in game.good_roles():
            if role is not self:
                self.information.add(RolePresent(role))


class Nimue(Role):
    role_name = RoleName.NIMUE
    alignment = Alignment.GOOD

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _update(self, game: Game) -> None:
        for role in game.roles:
            if role is not self:
                self.information.add(RolePresent(role))


class Guinevere(Role):
    """Sees one true and one false relationship rumour ("A sees B")."""

    role_name = RoleName.GUINEVERE
    alignment = Alignment.GOOD

    _unseeable = (RoleName.GUINEVERE, RoleName.MORDRED)

    def updaters(self, game: Game) -> List[Updater]:
        # Runs after base info (priority THREE) so that other roles' `seen`
        # information already exists to draw a true rumour from.
        return [(self._update, UpdaterPriority.THREE)]

    def _all_pair_seen(self, game: Game) -> List[PairSeen]:
        pairs: List[PairSeen] = []
        for role in game.roles:
            if role.role_name in self._unseeable:
                continue
            for info in role.information.seen:
                if info.seen.role_name not in self._unseeable:
                    pairs.append(PairSeen(role, info.seen))
        return pairs

    def _update(self, game: Game) -> None:
        truths = self._all_pair_seen(game)
        if not truths:
            return
        truth = game.rng.choice(truths)

        seeable = [r for r in game.roles if r.role_name not in self._unseeable]
        candidates = [
            PairSeen(r1, r2) for r1 in seeable for r2 in seeable if r1 is not r2
        ]
        lies = [
            c
            for c in candidates
            if not any(c.a is t.a and c.b is t.b for t in truths)
        ]
        if not lies:
            return
        lie = game.rng.choice(lies)

        self.information.add(lie)
        self.information.add(truth)
        self.information.add(
            Alert(
                "You see the following rumors, one of which is true, "
                "and one of which is false"
            )
        )

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        m["pairSeen"] = [s.replace("/", " sees ") for s in m["pairSeen"]]
        return m


class Gawain(Role):
    """Sees two pairs: one same-team and one different-team."""

    role_name = RoleName.GAWAIN
    alignment = Alignment.GOOD

    _unseeable = (RoleName.MORDRED,)

    def updaters(self, game: Game) -> List[Updater]:
        return [(self._update, UpdaterPriority.TEN)]

    def _same_team_from(self, roles: List[Role], game: Game):
        candidates = [
            r for r in roles if r is not self and r.role_name not in self._unseeable
        ]
        game.rng.shuffle(candidates)
        if len(candidates) < 2:
            return None
        return PairSeen(candidates[0], candidates[1])

    def _same_team_pair(self, game: Game):
        first, second = game.good_roles(), game.evil_roles()
        if game.rng.random() < 0.5:
            first, second = second, first
        return self._same_team_from(first, game) or self._same_team_from(second, game)

    def _different_team_pair(self, game: Game):
        good = [
            r for r in game.good_roles() if r is not self and r.role_name not in self._unseeable
        ]
        evil = [r for r in game.evil_roles() if r.role_name not in self._unseeable]
        if not good or not evil:
            return None
        good_role = game.rng.choice(good)
        evil_role = game.rng.choice(evil)
        if game.rng.random() < 0.5:
            return PairSeen(good_role, evil_role)
        return PairSeen(evil_role, good_role)

    def _update(self, game: Game) -> None:
        same = self._same_team_pair(game)
        if same is None:
            return
        diff = self._different_team_pair(game)
        if diff is None:
            return
        self.information.add(same)
        self.information.add(diff)

    def prepare_information(self) -> Dict[str, List[str]]:
        m = super().prepare_information()
        m["pairSeen"] = [
            f"{s.replace('/', ' and ')} are potentially allies (or enemies)"
            for s in m["pairSeen"]
        ]
        return m
