"""API-key resolution.

Precedence: an explicit ``BINGEARR_API_KEY`` env var wins. Otherwise a key is
generated once and persisted in the ``app_settings`` table so it survives
restarts. The effective key is cached in-process after first resolution.
"""

from __future__ import annotations

import logging
import secrets

from .config import settings
from .db.database import SessionLocal
from .models import AppSetting

log = logging.getLogger("bingearr.security")

_API_KEY_SETTING = "api_key"
_cached_key: str | None = None


def _generate() -> str:
    return secrets.token_hex(24)


def init_api_key() -> str:
    """Resolve (and if needed generate + persist) the effective API key."""
    global _cached_key

    if settings.api_key:
        _cached_key = settings.api_key
        return _cached_key

    with SessionLocal() as db:
        row = db.get(AppSetting, _API_KEY_SETTING)
        if row is None:
            key = _generate()
            db.add(AppSetting(key=_API_KEY_SETTING, value=key))
            db.commit()
            log.info("Generated and persisted a new API key.")
            _cached_key = key
        else:
            _cached_key = row.value

    return _cached_key


def current_api_key() -> str:
    return _cached_key if _cached_key is not None else init_api_key()
