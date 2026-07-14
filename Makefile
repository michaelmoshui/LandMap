# LandMap build system. Thin, cross-platform wrappers around docker compose.
# Every target runs in containers - no host Python/Node needed.

COMPOSE      := docker compose
COMPOSE_DEV  := docker compose -f docker-compose.dev.yml
COMPOSE_TEST := docker compose -f docker-compose.test.yml
COMPOSE_E2E  := docker compose -f docker-compose.e2e.yml

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo LandMap - available commands:
	@echo   make up            Build and start the full stack at http://localhost
	@echo   make dev           Start dev stack with hot reload at http://localhost:5173
	@echo   make down          Stop the stack
	@echo   make down-dev       Stop the dev stack
	@echo   make stop-host     Kill stray host dev servers holding the dev ports
	@echo   make logs          Tail logs for the running stack
	@echo   make build         Build all images
	@echo   make rebuild       Rebuild all images with no cache
	@echo   make test          Run all tests - unit and e2e
	@echo   make test-backend  Run backend unit tests with pytest
	@echo   make test-frontend Run frontend unit tests with Vitest
	@echo   make test-e2e      Run end-to-end tests with Playwright
	@echo   make lint          Lint backend and frontend
	@echo   make fmt           Auto-format backend and frontend
	@echo   make ingest-gva    Refresh GVA data snapshots from the open-data portals
	@echo   make ingest-boundaries  Refresh boundary polygons from open-data portals
	@echo   make clean         Stop everything and remove volumes

# ---- Run ----------------------------------------------------------------
.PHONY: up
up: ## Build and start the full production-like stack
	$(COMPOSE) up --build -d
	@echo LandMap is up. Open http://localhost

.PHONY: dev
dev: stop-host ## Start the dev stack with hot reload
	$(COMPOSE_DEV) up --build

.PHONY: down
down: ## Stop the production-like stack
	$(COMPOSE) down

.PHONY: down-dev
down-dev: stop-host ## Stop the dev stack (containers + stray host dev servers)
	$(COMPOSE_DEV) down

# `make dev` runs the frontend/backend in containers, but earlier sessions
# sometimes ran Vite/uvicorn directly on the host as a fallback. Those host
# processes are NOT stopped by `docker compose down`, so they keep holding
# the dev ports and block the next `make dev`. This finds whatever HOST
# process is listening on those ports and stops it, but only if it is a
# node/python dev server - so it never touches the containerized stack's
# root-owned docker-proxy, nor make/pgrep itself.
DEV_PORTS := 5173 8000
.PHONY: stop-host
stop-host: ## Kill stray host dev servers (vite/uvicorn) holding the dev ports
	@killed=""; \
	for port in $(DEV_PORTS); do \
	  for pid in $$(ss -ltnpH "sport = :$$port" 2>/dev/null \
	                | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u); do \
	    comm=$$(ps -o comm= -p $$pid 2>/dev/null); \
	    case "$$comm" in \
	      node|node.js|python|python3|uvicorn|vite) \
	        echo "Stopping host dev server on :$$port (pid $$pid, $$comm)"; \
	        kill $$pid 2>/dev/null || true; killed=1;; \
	    esac; \
	  done; \
	done; \
	[ -n "$$killed" ] || echo "No stray host dev servers found."

.PHONY: logs
logs: ## Tail logs
	$(COMPOSE) logs -f

.PHONY: build
build: ## Build all images
	$(COMPOSE) build

.PHONY: rebuild
rebuild: ## Rebuild all images from scratch
	$(COMPOSE) build --no-cache

# ---- Test ---------------------------------------------------------------
.PHONY: test
test: test-backend test-frontend test-e2e ## Run every test suite

.PHONY: test-backend
test-backend: ## Backend unit tests (pytest)
	$(COMPOSE_TEST) run --rm --build backend-tests

.PHONY: test-frontend
test-frontend: ## Frontend unit tests (Vitest)
	$(COMPOSE_TEST) run --rm --build frontend-tests

.PHONY: test-e2e
test-e2e: ## End-to-end tests (Playwright over the full stack)
	$(COMPOSE_E2E) up --build --abort-on-container-exit --exit-code-from e2e
	$(COMPOSE_E2E) down -v

# ---- Data ingestion ------------------------------------------------------
# Uses the dev compose file because it bind-mounts backend/app, so the
# refreshed snapshots in app/data/ land in the repo (commit them afterwards).
.PHONY: ingest-gva
ingest-gva: ## Refresh GVA layer snapshots from the open-data portals
	$(COMPOSE_DEV) run --rm --build --no-deps backend python -m app.ingest.gva

# ---- Quality ------------------------------------------------------------
.PHONY: lint
lint: ## Lint backend (ruff) and frontend (eslint + tsc)
	$(COMPOSE_TEST) run --rm --build backend-tests ruff check .
	$(COMPOSE_TEST) run --rm --build frontend-tests npm run lint

.PHONY: fmt
fmt: ## Auto-format backend (ruff) and frontend
	$(COMPOSE_TEST) run --rm --build backend-tests ruff format .

# ---- Data ---------------------------------------------------------------
# The backend-tests service mounts ./backend/app, so the refreshed
# backend/app/data/boundaries.geojson lands in the repo - review and commit it.
.PHONY: ingest-boundaries
ingest-boundaries: ## Refresh boundary polygons from government open-data portals
	$(COMPOSE_TEST) run --rm --build backend-tests python -m app.ingest.boundaries

# ---- Cleanup ------------------------------------------------------------
.PHONY: clean
clean: stop-host ## Stop all stacks and remove volumes
	-$(COMPOSE) down -v
	-$(COMPOSE_DEV) down -v
	-$(COMPOSE_E2E) down -v
