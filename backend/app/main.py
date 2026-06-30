"""Bingearr FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import __version__
from .config import settings
from .db.migrations import run_migrations
from .security import init_api_key
from .services.scheduler import run_due_schedules
from .api.routes import health, marathons, nexroll, servers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("bingearr")


async def scheduler_loop():
    """Tick once a minute, running any marathons whose schedule is due."""
    while True:
        try:
            ran = await asyncio.to_thread(run_due_schedules)
            if ran:
                log.info("Scheduler ran %d marathon(s)", ran)
        except Exception:  # noqa: BLE001 — a bad tick must not kill the loop
            log.exception("Scheduler tick failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    key = init_api_key()
    if not settings.api_key:
        # Only surface the key when we generated it (not when env-pinned).
        log.info("API key: %s", key)
    log.info("Bingearr %s ready on %s:%s", __version__, settings.host, settings.port)
    scheduler = asyncio.create_task(scheduler_loop())
    try:
        yield
    finally:
        scheduler.cancel()


app = FastAPI(title="Bingearr", version=__version__, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(servers.router)
app.include_router(marathons.router)
app.include_router(nexroll.router)

# Serve the built React app if present (single-container deploy). In dev the
# Vite server runs separately and proxies /api here, so this stays unmounted.
_static_dir = Path(__file__).resolve().parent.parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
