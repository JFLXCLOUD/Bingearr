"""The ``MediaServerClient`` interface.

Plex and Jellyfin differences live behind this so the rest of the app treats
them interchangeably. Phase 0 is read-only; write operations (create_playlist)
are declared here for the interface and implemented in Phase 1.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ConnectionInfo:
    ok: bool
    name: str | None = None
    version: str | None = None
    message: str | None = None


@dataclass
class LibrarySection:
    key: str
    title: str
    type: str  # movie | show | artist | photo
    item_count: int | None = None


@dataclass
class MediaItem:
    id: str  # Plex ratingKey / Jellyfin Item Id
    title: str
    type: str  # movie | show | episode
    year: int | None = None
    runtime_minutes: int | None = None
    guids: list[str] = field(default_factory=list)


class MediaServerClient(ABC):
    """Read/curate interface over a Plex or Jellyfin server."""

    @abstractmethod
    def test_connection(self) -> ConnectionInfo:
        """Verify credentials and return basic server info."""

    @abstractmethod
    def list_libraries(self) -> list[LibrarySection]:
        """List library sections."""

    @abstractmethod
    def list_items(self, library_key: str, limit: int = 100) -> list[MediaItem]:
        """List items in a library section."""

    # --- Phase 1 write op (default raises so read-only clients stay valid) ---
    def create_playlist(self, title: str, item_ids: list[str]) -> str:
        raise NotImplementedError(
            "create_playlist is a Phase 1 feature and not implemented yet."
        )
