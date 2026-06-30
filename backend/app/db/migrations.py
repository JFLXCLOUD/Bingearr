"""Lightweight in-app migration runner.

Tracks applied versions in a ``schema_migrations`` table and applies any
pending migrations in order. Migration 1 creates the initial schema from the
ORM metadata; later migrations should use explicit ``ALTER TABLE`` statements
so existing databases upgrade cleanly.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from .database import Base, engine

# Importing the models package registers every table on ``Base.metadata``.
from .. import models  # noqa: F401

log = logging.getLogger("bingearr.migrations")


def _ensure_version_table(conn: Connection) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version    INTEGER PRIMARY KEY,
                name       TEXT NOT NULL,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    )


def _applied_versions(conn: Connection) -> set[int]:
    rows = conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {row[0] for row in rows}


def _m001_initial(conn: Connection) -> None:
    Base.metadata.create_all(bind=conn)


def _columns(conn: Connection, table: str) -> set[str]:
    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return {row[1] for row in rows}


def _m002_schedule_columns(conn: Connection) -> None:
    # Idempotent: a fresh DB already has these from create_all (migration 1);
    # an existing DB gets them added here.
    existing = _columns(conn, "marathons")
    for col in ("last_run_at", "next_run_at"):
        if col not in existing:
            conn.execute(text(f"ALTER TABLE marathons ADD COLUMN {col} DATETIME"))


# (version, name, fn). Append new entries; never renumber existing ones.
MIGRATIONS = [
    (1, "initial schema", _m001_initial),
    (2, "marathon schedule bookkeeping columns", _m002_schedule_columns),
]


def run_migrations(eng: Engine = engine) -> None:
    with eng.begin() as conn:
        _ensure_version_table(conn)
        applied = _applied_versions(conn)
        pending = [m for m in MIGRATIONS if m[0] not in applied]
        for version, name, fn in pending:
            log.info("Applying migration %s: %s", version, name)
            fn(conn)
            conn.execute(
                text(
                    "INSERT INTO schema_migrations (version, name) VALUES (:v, :n)"
                ),
                {"v": version, "n": name},
            )
    if pending:
        log.info("Applied %d migration(s)", len(pending))
    else:
        log.info("Schema up to date")
