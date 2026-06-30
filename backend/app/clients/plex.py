"""Plex implementation of ``MediaServerClient`` (via python-plexapi)."""

from __future__ import annotations

import random

from .base import (
    CollectionInfo,
    ConnectionInfo,
    LibrarySection,
    MediaItem,
    MediaServerClient,
)


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

    def list_collections(self, library_key: str) -> list[CollectionInfo]:
        section = self.server.library.sectionByID(int(library_key))
        out: list[CollectionInfo] = []
        for col in section.collections():
            out.append(
                CollectionInfo(
                    id=str(col.ratingKey),
                    title=col.title,
                    item_count=getattr(col, "childCount", None),
                )
            )
        return out

    def expand_collection(self, collection_id: str) -> list[MediaItem]:
        collection = self.server.fetchItem(int(collection_id))
        members = list(collection.items())
        members.sort(key=lambda i: (getattr(i, "year", 0) or 0, getattr(i, "titleSort", i.title)))
        items: list[MediaItem] = []
        for it in members:
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

    def expand_show(
        self, show_id: str, order: str = "air", unwatched_only: bool = False
    ) -> list[MediaItem]:
        show = self.server.fetchItem(int(show_id))
        items: list[MediaItem] = []
        for ep in show.episodes():  # plexapi returns episodes in air order
            if unwatched_only and (getattr(ep, "viewCount", 0) or 0) > 0:
                continue
            season = getattr(ep, "parentIndex", 0) or 0
            number = getattr(ep, "index", 0) or 0
            duration = getattr(ep, "duration", None)
            runtime = int(duration / 60000) if duration else None
            items.append(
                MediaItem(
                    id=str(ep.ratingKey),
                    title=f"S{season:02d}E{number:02d} · {ep.title}",
                    type="episode",
                    runtime_minutes=runtime,
                )
            )
        return items

    def list_genres(self, library_key: str) -> list[str]:
        section = self.server.library.sectionByID(int(library_key))
        try:
            return [c.title for c in section.listFilterChoices("genre")]
        except Exception:  # noqa: BLE001 — library type may not support genres
            return []

    def smart_select(
        self,
        library_key: str,
        genre: str | None = None,
        watch: str = "all",
        minutes: int | None = None,
        max_items: int = 20,
    ) -> list[MediaItem]:
        section = self.server.library.sectionByID(int(library_key))
        filters: dict = {}
        if genre:
            filters["genre"] = genre
        if watch == "unwatched":
            filters["unwatched"] = True
        elif watch == "in_progress":
            filters["inProgress"] = True

        candidates = section.search(maxresults=600, **filters)
        random.shuffle(candidates)

        selected: list[MediaItem] = []
        total = 0
        for it in candidates:
            duration = getattr(it, "duration", None)
            runtime = int(duration / 60000) if duration else 0
            if minutes:
                if runtime <= 0 or total + runtime > minutes:
                    continue
                total += runtime
            chosen = MediaItem(
                id=str(it.ratingKey),
                title=it.title,
                type=it.type,
                year=getattr(it, "year", None),
                runtime_minutes=runtime or None,
            )
            selected.append(chosen)
            if minutes:
                if total >= minutes - 5:
                    break
            elif len(selected) >= max_items:
                break
        return selected

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
