# Bingearr backend

FastAPI + SQLite. See the repo root `ROADMAP.md` for the full plan.

## Run (dev)

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate     macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9494
```

On first start an API key is generated and printed in the log (and persisted in
`data/bingearr.db`). Pin your own with `BINGEARR_API_KEY` (see `.env.example`).

- Health (no auth): `GET /api/health`
- Interactive docs: `http://localhost:9494/docs`
- Everything under `/api/servers` and `/api/marathons` needs `X-Api-Key`.

## Layout

```
app/
  config.py         settings (env prefix BINGEARR_)
  security.py       API-key resolution (env or generated+persisted)
  db/               engine, session, in-app migration runner
  models/           SQLAlchemy ORM (servers, connections, marathons)
  clients/          MediaServerClient interface + read-only Plex impl
  api/              deps (auth), schemas, routes/
  services/         (business logic — fills in from Phase 1)
```

## Migrations

In-app and automatic on startup. Add a `(version, name, fn)` entry to
`MIGRATIONS` in `app/db/migrations.py`; never renumber existing ones.
