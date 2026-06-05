"""FastAPI application entry point."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="THavalon API",
    description="Role dealer and information service for in-person THavalon games.",
    version="0.1.0",
)
app.include_router(router)
