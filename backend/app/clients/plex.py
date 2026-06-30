"""Read-only Plex implementation of ``MediaServerClient`` (via python-plexapi)."""

from __future__ import annotations

from .base import ConnectionInfo, LibrarySection, MediaItem, MediaServerClient


class PlexClient(MediaServerClient):
    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._server = None  # connect lazily on first use

    @property
    def server(self):
        if self._server is None:
            # Imported lazily so the app imports cleanly without plexapi present.
            from plexapi.server import PlexServer

            self._server = PlexServer(self.base_url, self.token, timeout=self.timeout)
        return self._server

    def test_connection(self) -> ConnectionInfo:
        try:
            s = self.server
            return ConnectionInfo(ok=True, name=s.friendlyName, version=s.version)
        except Exception as exc:  # noqa: BLE001 — surface any client/transport error
            return ConnectionInfo(ok=False, message=str(exc))

    def list_libraries(self) -> list[LibrarySection]:
        sections = self.server.library.sections()
        out: list[LibrarySection] = []
        for sec in sections:
            count = None
            try:
                count = sec.totalSize
            except Exception:  # noqa: BLE001 — count is best-effort
                pass
            out.append(
                LibrarySection(
                    key=str(sec.key), title=sec.title, type=sec.type, item_count=count
                )
            )
        return out

    def list_items(
        self,
        library_key: str,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MediaItem]:
        section = self.server.library.sectionByID(int(library_key))
        filters: dict = {}
        if search:
            filters["title__icontains"] = search
        # Server-side pagination; guids are skipped here to keep browsing fast.
        results = section.search(
            maxresults=limit, container_start=offset, container_size=limit, **filters
        )
        items: list[MediaItem] = []
        for it in results:
            duration = getattr(it, "duration", None)
            runtime = int(duration / 60000) if duration else None
            items.append(
                MediaItem(
                    id=str(it.ratingKey),
                    title=it.title,
                    type=it.type,
                    year=getattr(it, "year", None),
                    runtime_minutes=runtime,
                )
            )
        return items

    def create_playlist(self, title: str, item_ids: list[str]) -> str:
        items = [self.server.fetchItem(int(i)) for i in item_ids]
        if not items:
            raise ValueError("Cannot create an empty playlist.")
        playlist = self.server.createPlaylist(title, items=items)
        return str(playlist.ratingKey)

    def delete_playlist(self, playlist_id: str) -> None:
        for pl in self.server.playlists():
            if str(pl.ratingKey) == str(playlist_id):
                pl.delete()
                return
