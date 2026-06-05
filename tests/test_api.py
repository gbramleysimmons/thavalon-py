"""Tests for the REST API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _roll(client: TestClient, size: int = 5) -> str:
    names = [f"p{i}" for i in range(size)]
    resp = client.post("/names", json={"names": names})
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body, body
    return body["id"]


def test_health(client: TestClient) -> None:
    assert client.get("/").json() == "Thavalon API"


def test_roll_and_fetch_info(client: TestClient) -> None:
    game_id = _roll(client, 5)
    assert client.get(f"/isGame/{game_id}").json() is True

    info = client.get(f"/game/info/{game_id}").json()
    assert len(info) == 5
    for player in info:
        assert set(player) == {"name", "role", "description", "information", "allegiance"}
        assert set(player["information"]) == {
            "alerts",
            "rolePresent",
            "seen",
            "pairSeen",
            "perfect",
        }
        assert player["allegiance"] in {"Good", "Evil"}


def test_info_for_unknown_id_is_empty(client: TestClient) -> None:
    assert client.get("/game/info/zzzz").json() == []
    assert client.get("/isGame/zzzz").json() is False


def test_unsupported_player_count_returns_error(client: TestClient) -> None:
    resp = client.post("/names", json={"names": ["a", "b", "c"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "error" in body
    assert "id" not in body


def test_gameover_is_idempotent(client: TestClient) -> None:
    game_id = _roll(client, 5)
    first = client.post(f"/gameover/{game_id}", json={"result": "Good Wins!", "record": True})
    assert first.json() is True
    second = client.post(f"/gameover/{game_id}")
    assert second.json() is False
    assert client.get(f"/isGame/{game_id}").json() is False


def test_currentgames_returns_newest_first(client: TestClient) -> None:
    ids = [_roll(client, 5) for _ in range(3)]
    recent = client.post("/currentgames", json={"numGames": 2}).json()
    assert recent == ids[::-1][:2]


def test_custom_game_roll(client: TestClient) -> None:
    custom = {
        "Merlin": True,
        "Lancelot": True,
        "Guinevere": True,
        "Mordred": True,
        "Oberon": True,
    }
    resp = client.post("/names", json={"names": [f"p{i}" for i in range(5)], "custom": custom})
    body = resp.json()
    assert "id" in body, body
    info = client.get(f"/game/info/{body['id']}").json()
    roles = sorted(p["role"] for p in info)
    assert roles == ["Guinevere", "Lancelot", "Merlin", "Mordred", "Oberon"]
