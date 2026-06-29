"""Media-server clients and the factory that picks one per server type."""

from __future__ import annotations

from ..config import settings
from ..models import MediaServer
from .base import MediaServerClient


def get_media_client(server: MediaServer) -> MediaServerClient:
    if server.type == "plex":
        from .plex import PlexClient

        return PlexClient(server.base_url, server.token, timeout=settings.plex_timeout)
    if server.type == "jellyfin":
        raise NotImplementedError(
            "Jellyfin client not implemented yet (planned after the Plex MVP)."
        )
    raise ValueError(f"Unknown media server type: {server.type!r}")


__all__ = ["MediaServerClient", "get_media_client"]
