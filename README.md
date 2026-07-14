# LandMap

An open, self-hostable web map of land information for the **Greater Vancouver
Area** - housing prices and demographics today, with forward-looking layers
(road construction, SkyTrain expansion, new high-rises) sourced from government
plans as the project grows. Municipality and neighborhood boundaries can be
toggled as map layers and selected by clicking them (or via search); selected
areas keep the normal map colors while all non-selected boundaries dim, once
at least one is selected. Lots are searchable too and highlight in distinct
colors. Boundary polygons are real government open data (Metro Vancouver
municipalities; Vancouver and Burnaby neighborhoods so far - see `SOURCES.md`),
refreshed with `make ingest-boundaries`; lots are sample data until parcel
ingestion lands.

## Stack

| Piece      | Choice                              | Why                                    |
|------------|-------------------------------------|----------------------------------------|
| Frontend   | React + Vite + TypeScript + MapLibre GL | Fast, open-source maps, no API tokens |
| Backend    | FastAPI (Python)                    | Lightweight, async, great for GeoJSON  |
| Database   | PostgreSQL + PostGIS                | First-class geospatial queries         |
| Proxy      | Caddy                               | One entrypoint + automatic HTTPS       |
| Containers | Docker + Docker Compose             | Reproducible, cross-platform           |

Everything runs in containers. You do **not** need Python or Node installed on
the host - only Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (with Docker Compose v2)
- `make` (optional but recommended). Without it, run the underlying
  `docker compose` commands shown in the [`Makefile`](./Makefile).

## Quick start

```bash
# Start the full production-like stack (builds images on first run)
make up
# -> open http://localhost

# ...or develop with hot reload
make dev
# -> frontend http://localhost:5173 , API docs http://localhost:8000/api/docs

# Stop
make down          # (make down-dev for the dev stack)
```

No configuration is required: `docker-compose.yml` ships with working defaults.

## Configuration

Defaults live in [`docker-compose.yml`](./docker-compose.yml). To override,
copy the sample env file and edit it:

```bash
cp .env.example .env            # macOS/Linux
Copy-Item .env.example .env     # Windows PowerShell
```

Key variables: database credentials, `BACKEND_CORS_ORIGINS`, and `DOMAIN`.

## Hosting on the internet

The Caddy proxy is the single public entrypoint (ports 80/443) and handles TLS
automatically:

1. Point a DNS record at your server's public IP.
2. Open ports 80 and 443.
3. Set `DOMAIN=your.domain.com` in `.env`.
4. `make up` - Caddy fetches and renews HTTPS certificates for you.

For local-only use, leave `DOMAIN=:80` and browse `http://localhost`.

## Testing

```bash
make test            # all: backend unit + frontend unit + e2e
make test-backend    # pytest
make test-frontend   # Vitest
make test-e2e        # Playwright against the full stack
```

See [`tests/README.md`](./tests/README.md) for the strategy and layout.

## Project layout

```
LandMap/
  backend/            FastAPI service (+ unit tests in backend/tests/)
  frontend/           React + MapLibre app (+ unit tests in frontend/tests/)
  proxy/              Caddy reverse-proxy config
  tests/e2e/          Playwright end-to-end tests
  docker-compose.yml         production-like stack
  docker-compose.dev.yml     dev stack (hot reload)
  docker-compose.test.yml    unit test runners
  docker-compose.e2e.yml     end-to-end stack
  Makefile            build system (wraps docker compose)
  AGENTS.md / SKILL.md       guides for AI agents
```

## Roadmap

- [ ] Ingest real datasets into PostGIS (housing, demographics).
- [ ] Government-plan layers: road construction, SkyTrain, high-rises.
- [ ] Time slider for "planned" layers (what's coming and when).
- [ ] Self-hosted vector tiles to remove the OpenFreeMap dependency.
