"""Core enumerations for the THavalon domain model."""
from __future__ import annotations

from enum import Enum


class Alignment(str, Enum):
    GOOD = "Good"
    EVIL = "Evil"
    UNKNOWN = "Unknown"


class RoleName(str, Enum):
    """Every role that can appear in a game.

    The string values match the names used by the original API/frontend so that
    custom-game requests and serialized output stay compatible.
    """

    MERLIN = "Merlin"
    LANCELOT = "Lancelot"
    PERCIVAL = "Percival"
    GUINEVERE = "Guinevere"
    TRISTAN = "Tristan"
    ISEULT = "Iseult"
    ARTHUR = "Arthur"
    GALAHAD = "Galahad"
    TITANIA = "Titania"
    NIMUE = "Nimue"
    GAWAIN = "Gawain"

    MORDRED = "Mordred"
    MORGANA = "Morgana"
    MAELEGANT = "Maelegant"
    OBERON = "Oberon"
    AGRAVAINE = "Agravaine"
    COLGREVANCE = "Colgrevance"

    UNKNOWN = "Unknown"


class Card(str, Enum):
    """Cards a player may physically play on a mission."""

    PASS = "P"
    FAIL = "F"
    REVERSE = "R"


class UpdaterPriority(int, Enum):
    """Priority for information updaters.

    Updaters run in *descending* priority order, so ``TEN`` runs first and
    ``ONE`` runs last. Base information (e.g. who Merlin sees) is produced at
    ``TEN`` so that later, lower-priority updaters (Guinevere reading
    relationships at ``THREE``; Oberon/Titania/Hijack corrupting info at
    ``ONE``) operate on already-computed information.
    """

    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
