"""Marathon scheduling: recurrence math, recipe rebuild, and the due-run sweep.

Times are handled in the server's local time so a user's "03:00" means 3am
where Bingearr runs. The background loop in ``app.main`` calls
``run_due_schedules`` once a minute.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..clients import get_media_client
from ..db.database import SessionLocal
from ..models import Marathon, MediaServer
from .builder import PushError, push_marathon, replace_items_from_media

log = logging.getLogger("bingearr.scheduler")


def _parse_hhmm(value: str | None) -> tuple[int, int]:
    try:
        hh, mm = (value or "03:00").split(":")
        return max(0, min(23, int(hh))), max(0, min(59, int(mm)))
    except Exception:  # noqa: BLE001 — fall back to a sane default
        return 3, 0


def compute_next_run(schedule: dict, after: datetime) -> datetime | None:
    """Next fire time strictly after ``after`` for a schedule config, or None."""
    freq = (schedule or {}).get("frequency", "off")
    if freq == "off":
        return None
    if freq == "hourly":
        return after + timedelta(hours=1)

    hh, mm = _parse_hhmm(schedule.get("time"))
    candidate = after.replace(hour=hh, minute=mm, second=0, microsecond=0)

    if freq == "daily":
        if candidate <= after:
            candidate += timedelta(days=1)
        return candidate

    if freq == "weekly":
        weekday = int(schedule.get("weekday", 0)) % 7
        days_ahead = (weekday - candidate.weekday()) % 7
        candidate += timedelta(days=days_ahead)
        if candidate <= after:
            candidate += timedelta(days=7)
        return candidate

    return None


def _resolve_recipe_items(db: Session, marathon: Marathon):
    """Re-resolve a rule/smart marathon's items from its stored recipe.

    Returns a list of MediaItem, or None for manual marathons (keep items).
    """
    if not marathon.rule_config:
        return None
    cfg = json.loads(marathon.rule_config)
    kind = cfg.get("kind")
    server = db.get(MediaServer, marathon.server_id)
    if server is None:
        raise PushError("The marathon's media server no longer exists.")
    client = get_media_client(server)

    if kind == "smart":
        return client.smart_select(
            cfg["library_key"],
            genre=cfg.get("genre") or None,
            watch=cfg.get("watch", "all"),
            minutes=cfg.get("minutes"),
        )
    if kind == "series":
        return client.expand_show(
            cfg["show_id"], unwatched_only=cfg.get("unwatched_only", False)
        )
    if kind == "collection":
        return client.expand_collection(cfg["collection_id"])
    return None


def rebuild_and_push(db: Session, marathon: Marathon) -> dict:
    """Re-resolve the recipe (if any), then (re)push the playlist to the server."""
    items = _resolve_recipe_items(db, marathon)
    if items is not None:
        if not items:
            raise PushError("The recipe produced no items (everything filtered out?).")
        replace_items_from_media(marathon, items)
        db.flush()
    return push_marathon(db, marathon)


def run_due_schedules(now: datetime | None = None) -> int:
    """Rebuild + push every marathon whose next_run_at has passed. Returns count run."""
    now = now or datetime.now()
    ran = 0
    with SessionLocal() as db:
        due = db.scalars(
            select(Marathon).where(
                Marathon.next_run_at.is_not(None), Marathon.next_run_at <= now
            )
        ).all()
        for marathon in due:
            schedule = json.loads(marathon.schedule) if marathon.schedule else {}
            try:
                result = rebuild_and_push(db, marathon)
                log.info("Scheduled rebuild of '%s': %s", marathon.name, result)
            except (PushError, Exception) as exc:  # noqa: BLE001 — never let one kill the sweep
                log.warning("Scheduled rebuild of '%s' failed: %s", marathon.name, exc)
                db.rollback()
            marathon.last_run_at = now
            marathon.next_run_at = compute_next_run(schedule, now)
            db.commit()
            ran += 1
    return ran
