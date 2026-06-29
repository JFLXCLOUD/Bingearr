# CLAUDE.md — Bingearr

> Standing context for AI coding agents. Read this before making changes. The full plan, data model, and integration specs live in `ROADMAP.md`.

## What Bingearr is

Bingearr is a self-hosted tool for the *Arr ecosystem that turns an existing
Plex or Jellyfin library into curated **binge experiences** — playlists,
marathons, and themed collections. It is the *consumption / curation* layer:
where Radarr and Sonarr acquire media, Bingearr decides **what to watch and in
what order**, then pushes that as a native playlist/collection back to the media
server so it appears in every client.

It is a **sibling project to NeXroll** (the author's preroll manager) and should
mirror NeXroll's architecture, distribution model, and UI language so the two
feel like one family.

### Honest positioning note
The canonical *Arr apps (Sonarr, Radarr, etc.) are .NET forks of a shared
Servarr codebase. Bingearr is **not** that, and does not need to be — NeXroll
isn't either. "Part of the ecosystem" here means: the `-arr` name, the same
self-hosted deploy story, API-key auth, and first-class integration with the
other Arrs (Radarr/Sonarr) and NeXroll. Don't try to fork Servarr.

## Tech stack (mirror NeXroll)

- **Backend:** Python + FastAPI
- **Database:** SQLite (single-file, migrations handled in-app)
- **Frontend:** React web UI, matching NeXroll's design language
- **Media server clients:** `python-plexapi` for Plex; Jellyfin REST API
- **External Arr clients:** Radarr/Sonarr v3 REST API (for recipe gap-filling)
- **Suggested default port:** `9494` (NeXroll uses 9393 — do not collide)

## Distribution (same triple as NeXroll, in this order)

1. **Docker** image + `docker-compose.yml` (build this first)
2. **Windows** installer with optional background service + tray app
3. **Unraid** Community Applications template

## Proposed repo structure

```
/backend        FastAPI app (api/, services/, clients/, models/, db/)
/frontend       React app
/docker         Dockerfile, compose, healthcheck
/docs           ROADMAP.md, data model, integration specs
/windows        installer + service + tray (later milestone)
```

## Conventions

- API-key auth on Bingearr's own API (`X-Api-Key` header), like the Arrs.
- Marathons/recipes are defined by **external metadata IDs** (TMDB / TVDB /
  IMDb), never local file paths or server-specific rating keys. This is what
  makes them portable and shareable. See `ROADMAP.md` → Recipe format.
- Let the media server own playback. Bingearr creates **native playlists /
  collections**; it does not orchestrate playback itself.
- Keep media-server differences behind a `MediaServerClient` interface so Plex
  and Jellyfin are interchangeable to the rest of the app.

## How to run (dev — fill in as scaffolding lands)

```
# backend
cd backend && uvicorn app.main:app --reload --port 9494
# frontend
cd frontend && npm run dev
```

## Current focus — Milestone 1 (thin MVP)

Default scope decisions (override if the author says otherwise):
- **Plex first**, Jellyfin second (matches NeXroll maturity).
- MVP = **manual marathon builder + franchise/series-order rule**, pushed to
  Plex as a native playlist. No smart/time-box engine yet.

Milestone 1 checklist lives in `ROADMAP.md` → Phase 1.

## Non-goals (for now)

- No transcoding, downloading, or playback engine of our own.
- No replacing Plex/Jellyfin clients.
- No Servarr/.NET fork.
