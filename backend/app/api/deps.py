"""Shared API dependencies."""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

from ..security import current_api_key


def require_api_key(
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> None:
    """Reject requests without a valid ``X-Api-Key`` header (constant-time compare)."""
    expected = current_api_key()
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
