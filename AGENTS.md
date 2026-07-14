# AGENTS.md - Operating guide for AI agents on LandMap

This repository is **vibe-coded**: most changes are made by AI agents. Read this
file fully before making changes. It is the source of truth for how to work here.

## What LandMap is

A web map of land information for the **Greater Vancouver Area (`gva`)** and
the **Greater Toronto Area (`gta`)**. Planned layers:

- Baseline: housing prices, demographics.
- Forward-looking (from government sources): road construction, transit
  expansion (SkyTrain, Ontario Line), upcoming high-rise developments -
  surfaced *before* work begins.

Regions and their open-data portals live in **`SOURCES.md`**. The backend
parses it at request time (`app/services/sources.py`; the file is bind-mounted
into the backend container) and serves it via `GET /api/regions` and
`GET /api/sources?region=`. Layers carry a `region` field and can be filtered
with `GET /api/layers?region=`. To add a region or portal, edit SOURCES.md - a
`## <Region Name> (ACRONYM)` section plus `* **Name**` bullets with nested
`**Description**`/`**Endpoint**` fields is all the parser needs (add a
viewport in `_REGION_VIEWPORTS` for a new region).

Layer data is served from **ingested GeoJSON snapshots** committed under
`backend/app/data/<region>/` and refreshed with `make ingest-gva` (see
`backend/app/ingest/`). The GVA layers carry real data pulled from the
SOURCES.md portals (City of Vancouver Opendatasoft, StatCan census, OSM
Overpass); layers without a snapshot (currently all of the GTA) fall back to
built-in sample data. PostGIS wiring is scaffolded for when layers outgrow
flat files.

## Architecture (keep this mental model)

```
Browser --HTTP(S)--> Caddy (proxy, :80/:443)
                       |-- /       --> frontend (React + Vite + MapLibre, nginx)
                       \-- /api/*  --> backend  (FastAPI, uvicorn)
                                           \--> db (PostGIS)
```

- `frontend/` - React + TypeScript + Vite + MapLibre GL. Renders the map and
  fetches layers from `/api`.
- `backend/` - FastAPI service. Serves GeoJSON layers/features. PostGIS-backed
  (DB wiring scaffolded; endpoints currently return sample data).
- `proxy/` - Caddy config. Single entrypoint, automatic HTTPS in production.
- `tests/e2e/` - Playwright end-to-end tests against the running stack.
- Unit tests live **inside each service** (`backend/tests/`, `frontend/tests/`).

## When you hit a bug (READ THIS FIRST)

Before debugging **any** new issue - whether the user reports it or you hit it
yourself - **open `BUG_LOG.md` and scan it for related symptoms.** Several
problems in this project recur (file encoding, shell quoting, container/engine
state), and the log already records the root cause and fix for each.

Workflow:

1. Reproduce/observe the symptom.
2. Search `BUG_LOG.md` for matching error text or behavior. If found, apply the
   documented fix.
3. If it is a new bug, fix it, then **add an entry to `BUG_LOG.md`** (newest
   first) with **Symptoms**, **Root cause**, and **Fix**.
4. Add/extend a test that would have caught it, when practical.

## Golden rules for agents

1. **Everything runs in Docker.** Do not assume Python/Node are installed on the
   host. Use `make` targets, which wrap `docker compose`. See `README.md`.
2. **Keep the stack lightweight and self-hostable.** No proprietary/paid
   services (no Google Maps/Mapbox tokens). MapLibre + open tiles only.
3. **Never commit secrets.** `.env` is git-ignored; only `.env.example` is
   tracked. Compose must keep working with defaults and no `.env`.
4. **Tests are not optional.** Any behavior change needs matching tests:
   - Backend logic -> `backend/tests/unit/`
   - Frontend logic/components -> `frontend/tests/unit/`
   - User-visible flows across the stack -> `tests/e2e/`
   Run `make test` before declaring work done.
5. **Preserve the layer contract.** Frontend and backend agree on the API shape
   in `backend/app/schemas`. If you change it, update both sides and the e2e
   tests in the same change.
6. **Pin dependencies.** Add versions; don't float to "latest".
7. **Small, verifiable steps.** Prefer changes you can prove with `make test`.
8. **Consult `BUG_LOG.md` first when debugging, and log new bugs there** (see the
   section above).

## Common commands

| Task                         | Command              |
|------------------------------|----------------------|
| Start full stack (prod-like) | `make up`            |
| Start dev (hot reload)       | `make dev`           |
| Stop everything              | `make down`          |
| All tests                    | `make test`          |
| Backend unit tests           | `make test-backend`  |
| Frontend unit tests          | `make test-frontend` |
| End-to-end tests             | `make test-e2e`      |
| Lint / format                | `make lint` / `make fmt` |
| Refresh GVA data snapshots   | `make ingest-gva`    |

## Definition of done

- `make lint` passes.
- `make test` passes (unit + e2e).
- New/changed behavior is covered by tests.
- New bugs are recorded in `BUG_LOG.md`.
- Docs updated if commands, env vars, or the API contract changed.

See `SKILL.md` for deeper, task-specific playbooks.
