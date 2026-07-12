# AGENTS.md - Operating guide for AI agents on LandMap

## What LandMap is

A web map of land information for the **Greater Vancouver Area**. Planned layers:

- Baseline: housing prices, demographics.
- Forward-looking (from government sources): road construction, SkyTrain
  expansion, upcoming high-rise developments - surfaced *before* work begins.

The current codebase is a **scaffold**: the plumbing (map, API, DB, tests,
containers) is in place with sample data. Real data ingestion comes later.

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
6. **Pin dependencies.** Add versions; don't float to "latest" silently.
7. **Small, verifiable steps.** Prefer changes you can prove with `make test`.

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

## Definition of done

- `make lint` passes.
- `make test` passes (unit + e2e).
- New/changed behavior is covered by tests.
- Docs updated if commands, env vars, or the API contract changed.

See `SKILL.md` for deeper, task-specific playbooks.
