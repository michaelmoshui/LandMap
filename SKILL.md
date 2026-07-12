# SKILL.md - LandMap task playbooks

Practical, repeatable recipes for building LandMap. Pair this with `AGENTS.md`
(rules and architecture). All commands assume Docker + `make` on the host.

---

## Playbook: Add a new map layer (end to end)

A "layer" is a themed dataset shown on the map (e.g. `housing-prices`,
`skytrain-expansion`). Follow all steps in one change.

1. **Define/confirm the contract.** Layers are `LayerMeta`; features are GeoJSON
   `FeatureCollection`. See `backend/app/schemas/layers.py`.
2. **Backend data source.** Add the layer to the registry in
   `backend/app/services/layers.py` (id, title, description, category) and a
   function returning its `FeatureCollection`. Start with sample data; wire
   PostGIS later.
3. **Expose it.** Routes already generic:
   - `GET /api/layers` lists all layers.
   - `GET /api/layers/{layer_id}/features` returns the FeatureCollection.
   No new route needed unless the shape differs.
4. **Backend test.** Add a case in `backend/tests/unit/` asserting the layer
   appears in the list and returns valid GeoJSON.
5. **Frontend.** The layer picker reads `/api/layers` automatically. Add styling
   in `frontend/src/map/layerStyles.ts` if the geometry needs a custom look.
6. **Frontend test.** Add/extend a Vitest test in `frontend/tests/unit/`.
7. **E2E.** Extend `tests/e2e/tests/` to toggle the new layer and assert it
   renders / the request succeeds.
8. `make test` must pass.

---

## Playbook: Wire a layer to real PostGIS data

1. Add a SQLAlchemy model under `backend/app/models/` (geometry via GeoAlchemy2).
2. Add a migration approach (start simple: create tables on startup guarded by a
   flag; introduce Alembic when schemas stabilize).
3. Add an ingestion script under `backend/app/ingest/` that pulls from the
   government/open-data source and upserts rows. Keep it idempotent.
4. Replace the sample function in `services/layers.py` with a DB query that
   returns GeoJSON (`ST_AsGeoJSON`).
5. Tests: unit-test the transform with a fixture; the DB-backed path is covered
   by e2e against the compose `db` service.

---

## Playbook: Add a backend endpoint

1. Add a router module in `backend/app/api/routes/` and include it in
   `backend/app/api/router.py`.
2. Define request/response models in `backend/app/schemas/`.
3. Add unit tests in `backend/tests/unit/` using FastAPI's `TestClient`.
4. Run `make test-backend`.

---

## Playbook: Add a frontend component

1. Component in `frontend/src/components/`; keep map logic in `frontend/src/map/`.
2. Co-locate types; reuse the API client in `frontend/src/api/client.ts`.
3. Vitest test in `frontend/tests/unit/`.
4. Run `make test-frontend`.

---

## Playbook: Prepare for internet hosting

1. Point a DNS A record at your server's public IP.
2. Open ports 80 and 443 on the server/router.
3. Set `DOMAIN=your.domain.com` in `.env`.
4. `make up`. Caddy obtains and renews HTTPS certificates automatically.
5. Verify: `make test-e2e` (locally) and load `https://your.domain.com`.

---

## Debugging tips

- Logs: `make logs` (all) or `docker compose logs -f backend`.
- Backend shell: `docker compose exec backend sh`.
- DB shell: `docker compose exec db psql -U landmap landmap`.
- API docs (dev): FastAPI auto-docs at `/api/docs`.
- If a build is stale: `make rebuild`.

## Conventions

- Python: FastAPI + Pydantic v2, `ruff` for lint/format, `pytest` for tests.
- TypeScript: strict mode, `vitest` for tests, functional React components.
- Keep functions small and typed. Prefer pure functions for data transforms so
  they are trivially unit-testable.
