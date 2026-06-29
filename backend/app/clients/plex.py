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

    def list_items(self, library_key: str, limit: int = 100) -> list[MediaItem]:
        section = self.server.library.sectionByID(int(library_key))
        items: list[MediaItem] = []
        for it in section.all()[:limit]:
            duration = getattr(it, "duration", None)
            runtime = int(duration / 60000) if duration else None
            guids = [g.id for g in getattr(it, "guids", []) if getattr(g, "id", None)]
            items.append(
                MediaItem(
                    id=str(it.ratingKey),
                    title=it.title,
                    type=it.type,
                    year=getattr(it, "year", None),
                    runtime_minutes=runtime,
                    guids=guids,
                )
            )
        return items
