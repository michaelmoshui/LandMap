# Testing

LandMap has a layered test strategy. All tests run in containers - no local
Python/Node required.

## Layers

| Layer            | Location             | Tool       | What it covers                                  |
|------------------|----------------------|------------|-------------------------------------------------|
| Backend unit     | `backend/tests/`     | pytest     | API endpoints, layer service, data transforms   |
| Frontend unit    | `frontend/tests/`    | Vitest     | API client, pure map helpers, React components   |
| End-to-end (e2e) | `tests/e2e/`         | Playwright | Full stack through the proxy (browser + API)    |

Unit tests are **specific**: they live next to the service they test and target
small units in isolation. E2E tests are **broad**: they boot the whole
production-like stack (db + backend + frontend + proxy) and drive it like a user.

## Running

```bash
make test            # everything: backend + frontend unit, then e2e
make test-backend    # pytest only
make test-frontend   # Vitest only
make test-e2e        # Playwright against the full stack
```

## Adding tests

- New backend behavior -> add to `backend/tests/unit/`.
- New frontend logic/component -> add to `frontend/tests/unit/`.
- New user-visible flow -> add a spec in `tests/e2e/tests/`.

See `SKILL.md` at the repo root for step-by-step playbooks.
