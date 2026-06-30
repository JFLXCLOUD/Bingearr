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


@dataclass
class CollectionInfo:
    id: str
    title: str
    item_count: int | None = None


class MediaServerClient(ABC):
    """Read/curate interface over a Plex or Jellyfin server."""

    @abstractmethod
    def test_connection(self) -> ConnectionInfo:
        """Verify credentials and return basic server info."""

    @abstractmethod
    def list_libraries(self) -> list[LibrarySection]:
        """List library sections."""

    @abstractmethod
    def list_items(
        self,
        library_key: str,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MediaItem]:
        """List/search items in a library section (paginated)."""

    # --- Rule-based building (default raises; Plex implements) ---
    def list_collections(self, library_key: str) -> list["CollectionInfo"]:
        """List a library's collections."""
        raise NotImplementedError

    def expand_collection(self, collection_id: str) -> list[MediaItem]:
        """Return a collection's items in release order."""
        raise NotImplementedError

    def expand_show(
        self, show_id: str, order: str = "air", unwatched_only: bool = False
    ) -> list[MediaItem]:
        """Return a show's episodes in order (optionally unwatched only)."""
        raise NotImplementedError

    def list_genres(self, library_key: str) -> list[str]:
        """Available genre filter values for a library."""
        raise NotImplementedError

    def smart_select(
        self,
        library_key: str,
        genre: str | None = None,
        watch: str = "all",
        minutes: int | None = None,
        max_items: int = 20,
    ) -> list[MediaItem]:
        """Pick items by genre/watch-state, packed to fit a runtime budget."""
        raise NotImplementedError

    # --- Write ops (default raises so read-only clients stay valid) ---
    def create_playlist(self, title: str, item_ids: list[str]) -> str:
        """Create a native playlist from ordered item ids; return its id."""
        raise NotImplementedError

    def delete_playlist(self, playlist_id: str) -> None:
        """Delete a native playlist by id (no-op if it no longer exists)."""
        raise NotImplementedError
