"""Health endpoints (unauthenticated — used by the Docker healthcheck)."""

from __future__ import annotations

from fastapi import APIRouter

from ... import __version__
from ..schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", app="bingearr", version=__version__)
