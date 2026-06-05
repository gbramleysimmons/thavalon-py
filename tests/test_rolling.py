"""Tests for the roll algorithm: ratios, vetoes, rerolls and duplicates."""
from __future__ import annotations

import random

import pytest

from app.domain.enums import Alignment, RoleName
from app.domain.ruleset import RollError, make_custom_ruleset, standard_ruleset

from .helpers import roll_custom, roll_standard

RATIOS = {5: (3, 2), 7: (4, 3), 8: (5, 3), 10: (6, 4)}


@pytest.mark.parametrize("size", [5, 7, 8, 10])
def test_standard_ratios(size: int) -> None:
    good, evil = RATIOS[size]
    for seed in range(25):
        game = roll_standard(size, seed)
        assert len(game.roles) == size
        assert len(game.good_roles()) == good
        assert len(game.evil_roles()) == evil
        # every player name is assigned exactly once
        assert sorted(r.player for r in game.roles) == sorted(f"p{i}" for i in range(size))


@pytest.mark.parametrize("size", [4, 6, 9, 11, 0])
def test_unsupported_sizes_rejected(size: int) -> None:
    with pytest.raises(RollError):
        standard_ruleset(size)


def test_make_game_unsupported_player_count() -> None:
    ruleset = standard_ruleset(5)
    with pytest.raises(RollError):
        ruleset.make_game(["a", "b", "c", "d"], random.Random(0))  # 4 players


def test_percival_vetoes_game_without_target() -> None:
    # Percival present but no Merlin/Morgana -> every reroll fails.
    roles = ["Percival", "Lancelot", "Guinevere", "Mordred", "Oberon"]
    with pytest.raises(RollError):
        roll_custom(roles, 5, seed=1)


def test_lone_percival_allows_game_without_target() -> None:
    roles = ["LonePercival", "Lancelot", "Guinevere", "Mordred", "Oberon"]
    game = roll_custom(roles, 5, seed=1)
    assert {r.role_name for r in game.good_roles()} == {
        RoleName.PERCIVAL,
        RoleName.LANCELOT,
        RoleName.GUINEVERE,
    }


def test_lover_vetoes_game_without_partner() -> None:
    roles = ["Tristan", "Lancelot", "Guinevere", "Mordred", "Oberon"]
    with pytest.raises(RollError):
        roll_custom(roles, 5, seed=1)


def test_lone_lover_allows_solo() -> None:
    roles = ["LoneTristan", "Lancelot", "Guinevere", "Mordred", "Oberon"]
    game = roll_custom(roles, 5, seed=1)
    assert any(r.role_name is RoleName.TRISTAN for r in game.good_roles())


def test_duplicates_allow_repeated_roles() -> None:
    # Tiny pools force duplicates when duplicates=True.
    ruleset = make_custom_ruleset(["Lancelot", "Mordred"], duplicates=True)
    game = ruleset.make_game([f"p{i}" for i in range(5)], random.Random(3))
    good_names = [r.role_name for r in game.good_roles()]
    evil_names = [r.role_name for r in game.evil_roles()]
    assert good_names == [RoleName.LANCELOT] * 3
    assert evil_names == [RoleName.MORDRED] * 2


def test_custom_requires_both_alignments() -> None:
    with pytest.raises(RollError):
        make_custom_ruleset(["Merlin", "Percival"], duplicates=False)


def test_custom_unknown_role_rejected() -> None:
    with pytest.raises(RollError):
        make_custom_ruleset(["NotARole", "Mordred"], duplicates=False)


def test_custom_alias_expansion() -> None:
    # "Lovers" expands to Tristan + Iseult.
    ruleset = make_custom_ruleset(
        ["Merlin", "Lovers", "Mordred", "Oberon"], duplicates=False
    )
    good_alignments = [f().alignment for f in ruleset.good_roles]
    assert all(a is Alignment.GOOD for a in good_alignments)
    assert len(ruleset.good_roles) == 3  # Merlin, Tristan, Iseult
