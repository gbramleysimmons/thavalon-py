"""FastAPI application entry point."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router

app = FastAPI(
    title="THavalon API",
    description="Role dealer and information service for in-person THavalon games.",
    version="0.1.0",
)
app.include_router(router)

# Mobile-friendly web UI for in-person play, served as static files at /app.
# The REST API (including the GET / health check) is left untouched.
_STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/app", StaticFiles(directory=str(_STATIC_DIR), html=True), name="ui")


@app.get("/ui", include_in_schema=False)
def ui_redirect() -> RedirectResponse:
    """Convenience redirect to the web UI."""
    return RedirectResponse(url="/app/")
