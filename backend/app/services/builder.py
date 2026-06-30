"""Marathon build/push logic — turns a persisted marathon into a server playlist."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from ..clients import get_media_client
from ..models import Marathon, MediaServer

log = logging.getLogger("bingearr.builder")


class PushError(Exception):
    """Raised when a marathon cannot be pushed to its media server."""


def push_marathon(db: Session, marathon: Marathon) -> dict:
    """Create (or rebuild) the native playlist for a marathon on its server."""
    if marathon.server_id is None:
        raise PushError("Marathon is not bound to a media server.")
    if not marathon.items:
        raise PushError("Marathon has no items to push.")

    server = db.get(MediaServer, marathon.server_id)
    if server is None:
        raise PushError("The marathon's media server no longer exists.")

    client = get_media_client(server)
    ordered = sorted(marathon.items, key=lambda i: i.position)
    item_ids = [it.server_item_id for it in ordered]

    # Rebuild semantics: drop the previous playlist if we made one before.
    if marathon.server_playlist_id:
        try:
            client.delete_playlist(marathon.server_playlist_id)
        except Exception:  # noqa: BLE001 — stale/removed playlist shouldn't block
            log.warning("Could not delete previous playlist %s", marathon.server_playlist_id)

    try:
        new_id = client.create_playlist(marathon.name, item_ids)
    except Exception as exc:  # noqa: BLE001 — normalize client/transport errors
        raise PushError(f"Plex rejected the playlist: {exc}") from exc

    marathon.server_playlist_id = new_id
    db.commit()
    log.info("Pushed marathon %s -> playlist %s (%d items)", marathon.id, new_id, len(item_ids))
    return {"ok": True, "server_playlist_id": new_id, "item_count": len(item_ids)}
