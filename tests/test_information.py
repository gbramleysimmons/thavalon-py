"""Tests for per-role information semantics."""
from __future__ import annotations

import pytest

from app.domain.enums import RoleName
from app.domain.information import Alert

from .helpers import find, roll_custom, roll_standard, seen_players

_DEFAULT_EVIL = {
    RoleName.MORDRED,
    RoleName.MORGANA,
    RoleName.MAELEGANT,
    RoleName.AGRAVAINE,
    RoleName.OBERON,
}


def _has_hijack(role) -> bool:
    return any(
        isinstance(a, Alert) and a.text == "You have Hijack!"
        for a in role.information.alerts
    )


# --- Property-style invariants over many standard games ----------------------


@pytest.mark.parametrize("size", [5, 7, 8, 10])
def test_default_evil_see_their_teammates(size: int) -> None:
    for seed in range(40):
        game = roll_standard(size, seed)
        evil = game.evil_roles()
        non_colg_evil = {r.player for r in evil if r.role_name is not RoleName.COLGREVANCE}
        for role in evil:
            if role.role_name not in _DEFAULT_EVIL:
                continue
            expected = non_colg_evil - {role.player}
            # Titania may add a false good player to one evil's seen, so use subset.
            assert expected <= seen_players(role)


@pytest.mark.parametrize("size", [5, 7, 8, 10])
def test_colgrevance_is_hidden_and_omniscient(size: int) -> None:
    for seed in range(40):
        game = roll_standard(size, seed)
        colg = find(game, RoleName.COLGREVANCE)
        if colg is None:
            continue
        other_evil = {r.player for r in game.evil_roles() if r is not colg}
        # Colgrevance perfectly knows every other evil.
        assert {p.seen.player for p in colg.information.perfect} == other_evil
        # No other evil sees Colgrevance.
        for role in game.evil_roles():
            if role is colg:
                continue
            assert colg.player not in seen_players(role)


@pytest.mark.parametrize("size", [5, 7, 8, 10])
def test_hijack_present_only_in_large_games(size: int) -> None:
    for seed in range(40):
        game = roll_standard(size, seed)
        hijack_holders = [r for r in game.roles if _has_hijack(r)]
        if size == 5:
            assert hijack_holders == []
        else:
            assert len(hijack_holders) == 1
            holder = hijack_holders[0]
            assert holder.role_name not in (RoleName.MORDRED, RoleName.COLGREVANCE)
            assert holder.alignment.value == "Evil"


@pytest.mark.parametrize("size", [5, 7, 8, 10])
def test_merlin_sees_evil_except_mordred_plus_lancelot(size: int) -> None:
    for seed in range(40):
        game = roll_standard(size, seed)
        merlin = find(game, RoleName.MERLIN)
        if merlin is None:
            continue
        expected = {r.player for r in game.evil_roles() if r.role_name is not RoleName.MORDRED}
        expected |= {r.player for r in game.good_roles() if r.role_name is RoleName.LANCELOT}
        # Oberon may plant one extra false "seen" on Merlin, so use a subset check.
        seen = seen_players(merlin)
        assert expected <= seen
        assert len(seen - expected) <= 1


# --- Exact-equality tests using Oberon/Titania-free custom games -------------


def test_merlin_exact_in_clean_game() -> None:
    game = roll_custom(["Merlin", "Lancelot", "Guinevere", "Mordred", "Morgana"], 5, seed=2)
    merlin = find(game, RoleName.MERLIN)
    morgana = find(game, RoleName.MORGANA)
    lancelot = find(game, RoleName.LANCELOT)
    mordred = find(game, RoleName.MORDRED)
    assert seen_players(merlin) == {morgana.player, lancelot.player}
    assert mordred.player not in seen_players(merlin)


def test_percival_sees_merlin_and_morgana() -> None:
    game = roll_custom(["Percival", "Merlin", "Lancelot", "Morgana", "Mordred"], 5, seed=4)
    percival = find(game, RoleName.PERCIVAL)
    merlin = find(game, RoleName.MERLIN)
    morgana = find(game, RoleName.MORGANA)
    assert seen_players(percival) == {merlin.player, morgana.player}


def test_lovers_see_each_other() -> None:
    game = roll_custom(["Tristan", "Iseult", "Lancelot", "Mordred", "Morgana"], 5, seed=6)
    tristan = find(game, RoleName.TRISTAN)
    iseult = find(game, RoleName.ISEULT)
    assert seen_players(tristan) == {iseult.player}
    assert seen_players(iseult) == {tristan.player}


def test_lone_lover_is_lonely() -> None:
    game = roll_custom(["LoneTristan", "Lancelot", "Guinevere", "Mordred", "Morgana"], 5, seed=7)
    tristan = find(game, RoleName.TRISTAN)
    assert seen_players(tristan) == set()
    assert any(a.text == "You are a sad and lonely lover" for a in tristan.information.alerts)


def test_arthur_knows_other_good_roles() -> None:
    game = roll_custom(
        ["Arthur", "Merlin", "Lancelot", "Guinevere", "Mordred", "Morgana", "Maelegant"],
        7,
        seed=8,
    )
    arthur = find(game, RoleName.ARTHUR)
    present = {rp.present.role_name for rp in arthur.information.role_present}
    expected = {r.role_name for r in game.good_roles() if r is not arthur}
    assert present == expected
    # Arthur only knows good roles.
    assert all(
        r.alignment.value == "Good" for r in game.roles if r.role_name in present
    )


def test_nimue_knows_every_other_role() -> None:
    game = roll_custom(
        ["Nimue", "Merlin", "Lancelot", "Guinevere", "Mordred", "Morgana", "Maelegant"],
        7,
        seed=9,
    )
    nimue = find(game, RoleName.NIMUE)
    present = sorted(rp.present.role_name.value for rp in nimue.information.role_present)
    expected = sorted(r.role_name.value for r in game.roles if r is not nimue)
    assert present == expected


def test_guinevere_has_one_true_one_false_rumor() -> None:
    game = roll_custom(
        ["Guinevere", "Merlin", "Tristan", "Iseult", "Mordred", "Morgana", "Maelegant"],
        7,
        seed=11,
    )
    guin = find(game, RoleName.GUINEVERE)
    assert len(guin.information.pair_seen) == 2

    unseeable = {RoleName.GUINEVERE, RoleName.MORDRED}
    real_pairs = {
        (r.player, s.seen.player)
        for r in game.roles
        if r.role_name not in unseeable
        for s in r.information.seen
        if s.seen.role_name not in unseeable
    }
    matches = sum(
        (info.a.player, info.b.player) in real_pairs for info in guin.information.pair_seen
    )
    assert matches == 1


def test_colgrevance_can_only_pass() -> None:
    # Faithful to the original: Colgrevance is a plain Role, so default cards.
    game = roll_custom(
        ["Merlin", "Lancelot", "Guinevere", "Mordred", "Colgrevance"], 5, seed=12
    )
    colg = find(game, RoleName.COLGREVANCE)
    assert [c.value for c in colg.card_options()] == ["P"]
