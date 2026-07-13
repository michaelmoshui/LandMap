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
	@echo   make logs          Tail logs for the running stack
	@echo   make build         Build all images
	@echo   make rebuild       Rebuild all images with no cache
	@echo   make test          Run all tests - unit and e2e
	@echo   make test-backend  Run backend unit tests with pytest
	@echo   make test-frontend Run frontend unit tests with Vitest
	@echo   make test-e2e      Run end-to-end tests with Playwright
	@echo   make lint          Lint backend and frontend
	@echo   make fmt           Auto-format backend and frontend
	@echo   make clean         Stop everything and remove volumes

# ---- Run ----------------------------------------------------------------
.PHONY: up
up: ## Build and start the full production-like stack
	$(COMPOSE) up --build -d
	@echo LandMap is up. Open http://localhost

.PHONY: dev
dev: ## Start the dev stack with hot reload
	$(COMPOSE_DEV) up --build

.PHONY: down
down: ## Stop the production-like stack
	$(COMPOSE) down

.PHONY: down-dev
down-dev: ## Stop the dev stack
	$(COMPOSE_DEV) down

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

# ---- Quality ------------------------------------------------------------
.PHONY: lint
lint: ## Lint backend (ruff) and frontend (eslint + tsc)
	$(COMPOSE_TEST) run --rm --build backend-tests ruff check .
	$(COMPOSE_TEST) run --rm --build frontend-tests npm run lint

.PHONY: fmt
fmt: ## Auto-format backend (ruff) and frontend
	$(COMPOSE_TEST) run --rm --build backend-tests ruff format .

# ---- Cleanup ------------------------------------------------------------
.PHONY: clean
clean: ## Stop all stacks and remove volumes
	-$(COMPOSE) down -v
	-$(COMPOSE_DEV) down -v
	-$(COMPOSE_E2E) down -v
