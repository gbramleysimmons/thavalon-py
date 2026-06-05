"""FastAPI application entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="THavalon API",
    description="Role dealer and information service for in-person THavalon games.",
    version="0.1.0",
)
app.include_router(router)

# Mobile-friendly web UI for in-person play. The REST API routes are registered
# above and take precedence; this static mount serves the game start screen at
# the site root and the UI's assets, so a bare domain lands on the game.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")
