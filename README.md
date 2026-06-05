# THavalon API (Python / FastAPI)

A **role dealer and information service** for in-person games of THavalon. The
server validates a player/role configuration, rolls roles, computes each
player's secret information, serves it per game id, and records the final
result. It does **not** run missions, proposals, voting, hijack, or
assassination — those are played in person by the humans.

This is a clean Python/FastAPI reimplementation of the original Kotlin REST API,
focused on readability and maintainability. Storage is in-memory only.

## Requirements
- Python 3.8+

## Setup
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Run
```bash
uvicorn app.main:app --reload --port 4444
```
Interactive API docs are then available at `http://localhost:4444/docs`.

## Test & lint
```bash
pytest          # run the test suite
ruff check .    # lint
```

## REST API
All bodies are JSON.

| Method & path | Purpose | Request | Response |
|---|---|---|---|
| `POST /names` | Roll a new game | `{ names: string[], custom?: {RoleName: bool}, duplicates?: bool }` | `{ id }` on success, or `{ error }` |
| `GET /game/info/{id}` | All players' roles + info | — | array of player objects (below); `[]` if unknown |
| `GET /isGame/{id}` | Does a game id exist? | — | `true` / `false` |
| `POST /gameover/{id}` | End game, clear it | `{ result?, record? }` (ignored) | `true` if the id still existed |
| `POST /currentgames` | Most recent game ids | `{ numGames }` | `string[]`, newest first |
| `GET /` | Health check | — | `"Thavalon API"` |

### Player object (`GET /game/info/{id}`)
```jsonc
{
  "name": "alice",
  "role": "Merlin",
  "description": "You are on the good team",
  "information": {
    "alerts": [],
    "rolePresent": [],
    "seen": ["You see bob as Evil (Or Lancelot)"],
    "pairSeen": [],
    "perfect": []
  },
  "allegiance": "Good"
}
```
The **first** player in the array is the randomized starting player.

> Note: the original API double-encoded the `information` field as a JSON
> *string*. This version returns it as a proper nested JSON object.

## Game configuration

| Players | Good | Evil | Mission sizes (1–5) |
|--------:|-----:|-----:|---------------------|
| 5       | 3    | 2    | 2, 3, 2, 3, 3       |
| 7       | 4    | 3    | 2, 3, 3, 4, 4       |
| 8       | 5    | 3    | 3, 4, 3, 4, 5       |
| 10      | 6    | 4    | 4, 5, 5, 5, 5       |

Mission sizes are informational for in-person play; the server does not enforce
them.

**Default rulesets** (when no `custom` is sent):
- Evil: `Mordred, Morgana, Maelegant, Oberon` (+`Agravaine` at 8, +`Agravaine, Colgrevance` at 10)
- Good: `Merlin, Percival, Guinevere, Tristan, Iseult, Lancelot` (+`Titania, Arthur` at 7+)

**Custom games** send `{ RoleName: bool }`. Aliases are expanded server-side:
`Lovers → Tristan + Iseult`, `Lone Lovers → LoneTristan + LoneIseult`,
`Lone Percival → LonePercival`, and `Duplicate Roles` enables duplicate draws.
Roles are partitioned into Good/Evil; at least one of each is required.

### Roll algorithm
Draw `numGood` good + `numEvil` evil roles (without replacement, or with
replacement when `duplicates`), validate the good/evil ratio and every role's
veto (`game_ok`), and reroll up to 100 times before failing. Vetoes include:
`Percival` requires a visible Merlin/Morgana; `Tristan`/`Iseult` require their
partner (the `Lone*` variants do not).

## Architecture
```
app/
  main.py                 FastAPI app
  api/                    routes, Pydantic schemas, dependencies
  domain/
    enums.py              Alignment, RoleName, Card, UpdaterPriority
    information.py        information types + InformationAggregator
    role.py               Role base + DefaultEvilRole
    roles/                one module per role group; ROLE_REGISTRY
    game.py               validation, information pipeline, player assignment
    ruleset.py            roll algorithm + standard/custom rulesets
  store/registry.py       in-memory game registry
tests/                    rolling, information-semantics, and API tests
```

Information is produced by **updaters** — `(callable, priority)` pairs that run
in descending priority order, so base information (e.g. who Merlin sees) is
computed before roles that read it (Guinevere) or corrupt it (Oberon, Titania,
Hijack).

## Scope
Only the complete, intended REST behavior is implemented. Out of scope: the
original's half-finished WebSocket "live game" / state machine, in-game mission
logic, and database/stats persistence (so `gameover` simply clears the game).
Galahad is a plain Good role and Nimue is information-only, matching the
original server.
