# NeXroll ↔ Bingearr integration contract

Bingearr talks to a small, **stable public API on NeXroll** (not its internal
endpoints). You own both projects, so add these four routes to NeXroll. Bingearr
already implements the calling side (`app/clients/nexroll.py`).

- **Auth:** `X-Api-Key` header. Use a NeXroll-issued integration key; Bingearr
  stores it as a `NeXrollConnection` (`base_url` + `api_key`).
- **Base path:** `/api/integration`
- All responses are JSON.

## Endpoints

### `GET /api/integration/status`
Health + version probe.
```json
{ "ok": true, "version": "2.3.1", "server_connected": true }
```

### `GET /api/integration/prerolls`
The prerolls a user can attach to a marathon.
```json
[
  { "id": "1", "name": "Cinema Intro", "type": "category" },
  { "id": "2", "name": "Marvel Logo Sting", "type": "sequence" }
]
```
`type` is `category` or `sequence`. `id` is a string.

### `POST /api/integration/apply`
Apply a preroll to the connected media server. Called when a marathon with a
preroll is **activated**.
```json
// request
{ "ref": "category:1", "server": "JFLX" }
// response
{ "applied": true, "message": "Applied category:1 to JFLX" }
```
`ref` is `"{type}:{id}"`. `server` is the Bingearr media-server name (advisory;
NeXroll may apply to its own connected server).

### `POST /api/integration/clear`
Revert to NeXroll's normal preroll schedule. Called on **teardown**.
```json
{ "applied": false, "message": "Reverted to NeXroll's normal schedule" }
```

## Bingearr flow

1. User connects NeXroll in **Settings** (`base_url` + `api_key`) → `status`.
2. In the marathon builder, the **Preroll** card lists `prerolls`; the chosen
   one is stored on the marathon (`preroll_ref`).
3. **Apply now** → `POST /apply` with the marathon's `ref` + media-server name.
   **Clear** → `POST /clear`.

## Cross-promo (the "help share" idea)

Ship a **Bingearr promo** preroll users can add in NeXroll, and a **NeXroll
promo** entry in Bingearr — discovery in both directions. The fake NeXroll used
in development already lists a "Bingearr Promo" preroll as an example.

## Verifying without the real app

`docs`-adjacent dev note: a fake NeXroll implementing exactly this contract is
used to test Bingearr's side end-to-end (status, prerolls, apply, clear).
