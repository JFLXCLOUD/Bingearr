# Bingearr — Roadmap & Spec

Binge-experience builder for Plex & Jellyfin. Sibling to NeXroll. Self-hosted,
Docker + Windows + Unraid.

---

## 1. Vision

Most *Arr tools live on the acquisition side. Bingearr is the curation layer:
take a library you already own and turn it into playlists, marathons, and
themed collections, then push them back to the server as native playlists or
collections. The two differentiators are **NeXroll preroll integration** and
**portable, shareable recipes that can auto-fill gaps via Radarr/Sonarr**.

---

## 2. Core feature set

- Connect to Plex and/or Jellyfin: read library, watch state; create native
  playlists/collections.
- Marathon builder, three modes:
  - **Manual** — pick items, set order.
  - **Rule-based** — franchise (chronological or release order), full series in
    air/DVD order, genre / actor / director marathons.
  - **Time-boxed** — fit a runtime budget ("a 4-hour Sunday block").
- Watch-state aware: unwatched-only, continue-where-left-off, skip-filler.
- Attach a **NeXroll preroll** to a marathon (intro that plays before it).
- **Export/import recipes** by metadata ID; resolve against the local library;
  hand missing items to Radarr/Sonarr.
- (Later) Community hub to browse and share recipes.

---

## 3. Data model

### Connection-type tables
- **MediaServer** — `id, type(plex|jellyfin), name, base_url, token_or_apikey,
  user_id, enabled`
- **NeXrollConnection** — `id, base_url, api_key, enabled`
- **ArrConnection** — `id, type(radarr|sonarr), base_url, api_key, enabled`

### Marathon (a built, server-bound experience)
- `id, name, description, server_id`
- `type(manual|rule|timeboxed)`
- `ordering(chronological|release|air|dvd|custom)`
- `watch_filter(all|unwatched|in_progress)`
- `rule_config` (JSON; see below)
- `preroll_ref` (NeXroll category/sequence id, nullable)
- `target_kind(playlist|collection)`
- `server_playlist_id` (set after push, nullable)
- `schedule` (nullable; reuse NeXroll-style recurrence later)
- `created_at, updated_at`

### MarathonItem (resolved local item)
- `id, marathon_id, position`
- `server_item_id` (Plex ratingKey / Jellyfin Item Id)
- `title, runtime_minutes, watched`

### rule_config (JSON examples)
```json
{ "kind": "franchise", "tmdb_collection_id": 86311, "order": "chronological" }
{ "kind": "series", "tvdb_id": 81189, "order": "air", "unwatched_only": true }
{ "kind": "timebox", "minutes": 240, "genre": "Horror", "unwatched_only": true }
```

### Recipe (portable, shareable — the export unit)
```json
{
  "schema_version": 1,
  "name": "MCU — Chronological",
  "author": "someone",
  "description": "Every MCU film in story order.",
  "ordering": "custom",
  "preroll_hint": "marvel-intro",
  "tags": ["marvel", "movies", "chronological"],
  "items": [
    { "source": "tmdb", "type": "movie", "id": 1771, "title": "Captain America: The First Avenger", "year": 2011 },
    { "source": "tmdb", "type": "movie", "id": 271969, "title": "Captain Marvel", "year": 2019 }
  ]
}
```
Recipes reference **external IDs only** — never file paths or rating keys.
TV episodes use `{ "source":"tvdb", "type":"episode", "id":..., "season":..., "episode":... }`.

---

## 4. NeXroll integration API

Add a small, **stable public API on NeXroll** (you own both projects) instead
of Bingearr poking internal endpoints. Auth via `X-Api-Key`.

- `GET  /api/integration/status` → `{ ok, version, server_connected }`
- `GET  /api/integration/prerolls` → `[ { id, name, type(category|sequence) } ]`
- `POST /api/integration/apply` → body `{ ref, server }`; applies that preroll
  to the connected media server; returns `{ applied, message }`
- `POST /api/integration/clear` → reverts to NeXroll's normal schedule

**Bingearr flow:** when a marathon with `preroll_ref` becomes active, call
`apply`; on teardown, call `clear`. Store NeXroll `base_url + api_key` as a
`NeXrollConnection`.

**Cross-promo (the "help share" idea):** ship a Bingearr promo preroll users can
add in NeXroll, and a NeXroll promo in Bingearr — discovery in both directions.

---

## 5. Recipe resolution & gap-fill

1. Import recipe JSON.
2. For each item, match against the media server by external id
   (Plex: GUID match; Jellyfin: `ProviderIds`).
3. **Found** → add to `MarathonItem` in order. **Missing** → collect.
4. If an `ArrConnection` exists, push missing items to Radarr (movies) /
   Sonarr (series/episodes) by external id; mark pending.
5. Re-resolve on a schedule until complete; create/update the native playlist.

This closes the loop with the rest of the stack and is the strongest reason
Bingearr belongs in the ecosystem.

---

## 6. Phased roadmap

### Phase 0 — Foundation ✅
- [x] Repo scaffold (`backend/`, `frontend/`, `docker/`) — docs still at repo root
- [x] FastAPI app + SQLite + migrations + `X-Api-Key` auth
- [x] `MediaServerClient` interface; Plex implementation (read-only)
- [x] React UI shell matching NeXroll
- [x] Dockerfile + compose + healthcheck

### Phase 1 — MVP (current focus)
- [ ] Plex connection UI (URL + token / sign-in)
- [ ] Browse library; manual marathon builder (pick + order)
- [ ] Rule: franchise/series order (TMDB collection / TVDB series)
- [ ] Push marathon to Plex as a **native playlist**
- [ ] Persist marathons; edit/rebuild/delete

### Phase 2 — Smart builder
- [ ] Time-boxed builder (runtime budget)
- [ ] Watch-state filters (unwatched / continue / skip-filler)
- [ ] Genre / actor / director rules
- [ ] Optional scheduling (NeXroll-style recurrence)

### Phase 3 — NeXroll prerolls
- [ ] Add the NeXroll integration API (above) on the NeXroll side
- [ ] `NeXrollConnection` + attach preroll to a marathon
- [ ] Apply/clear on marathon activation

### Phase 4 — Portable recipes + gap-fill
- [ ] Recipe export/import (schema v1)
- [ ] Resolve recipe against library; missing-item report
- [ ] Radarr/Sonarr connections + request missing items
- [ ] Re-resolve loop

### Phase 5 — Sharing hub
- [ ] Browse/search/share recipes
- [ ] One-click import → resolve → gap-fill

### Packaging (ongoing, in order)
- [ ] Docker (Phase 0) → [ ] Windows installer + service + tray → [ ] Unraid template

### Jellyfin
- [ ] Jellyfin `MediaServerClient` implementation (after Plex MVP proves the model)

---

## 7. Open decisions (defaults chosen — override freely)

- **Plex first**, Jellyfin second.
- **Thin MVP**: manual + franchise/series order only before the smart engine.
- "Marathon" = playlist + optional preroll + optional schedule. Keep the term
  in the data model; "playlist" is the thing pushed to the server.
