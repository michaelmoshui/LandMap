# BUG_LOG.md

A running log of bugs encountered in LandMap and how they were resolved. Newest
first. **Before debugging a new issue, scan this file for related symptoms.**

Each entry records:
- **Symptoms** - what was observed (error text, behavior).
- **Root cause** - the underlying reason.
- **Fix** - what resolved it (and how to avoid it).

---

## BUG-010: Ingested GeoJSON snapshots silently absent from git (`data/` ignore rule)

- **Symptoms**
  - `backend/app/data/gva/*.geojson` exists and is served locally, but never
    shows up in `git status`, so a fresh clone (and any Docker image built in
    CI) would quietly fall back to sample data with no error.
- **Root cause**
  - `.gitignore` has a bare `data/` rule meant for Docker *volume* mounts,
    which matches **any** directory named `data` at any depth - including the
    committed layer snapshots under `backend/app/data/`.
- **Fix**
  - Added `!backend/app/data/` right below the `data/` rule.
  - When adding new generated-but-committed artifacts, run
    `git check-ignore -v <path>` to confirm they are actually trackable;
    "no diff" after creating files is a red flag, not a success.

---

## BUG-009: `make dev` fails with `address already in use` on :5173 (host Vite survives `make down`)

- **Symptoms**
  - `make dev` aborts with
    `failed to bind host port 0.0.0.0:5173/tcp: address already in use`.
  - `make down` does **not** fix it; `ss -ltnp | grep :5173` shows a host
    `node .../node_modules/.bin/vite` process (not a container).
- **Root cause**
  - An earlier session ran Vite directly on the host as a fallback (see
    BUG-007). `make down` / `down-dev` call `docker compose down`, which only
    stops containers, so the host Vite keeps holding 5173 and blocks the
    containerized frontend from binding.
- **Fix**
  - `make stop-host` kills host dev servers listening on the dev ports
    (5173/8000). It only kills node/python listeners, so it never touches the
    containerized stack's root-owned `docker-proxy`. It is now a prerequisite
    of `make dev`, `make down-dev`, and `make clean`, so re-running `make dev`
    self-heals.
  - Rule of thumb: if `make down` doesn't free a port, it's a host process -
    `ss -ltnp | grep :<port>` then `make stop-host`.
  - Note: the cleanup must match by *port listener*, not `pgrep -f` on the
    repo path - a `.*` command-line pattern greedily self-matches the `make`/
    shell process running it and can kill your own shell.

---

## BUG-008: Root-owned empty `frontend/node_modules` blocks host `npm install`

- **Symptoms**
  - `npm ci` / `npm install` in `frontend/` failed with
    `EACCES: mkdir '/home/alex/landmap/frontend/node_modules/@adobe'`.
  - `frontend/node_modules` existed but was empty and owned by `root:root`.
- **Root cause**
  - A previous Docker run created the directory as root on the host (compose
    named-volume mount point). npm running as the regular user cannot write
    into a root-owned directory.
- **Fix**
  - The directory is empty, so the user (who owns the parent) can remove it:
    `rmdir frontend/node_modules`, then reinstall. If non-empty, it needs
    `sudo rm -rf`.

---

## BUG-007: Docker commands fail with `permission denied` on the docker socket (Linux)

- **Symptoms**
  - Every `make`/`docker compose` target failed with
    `permission denied while trying to connect to the docker API at
    unix:///var/run/docker.sock`.
- **Root cause**
  - `/var/run/docker.sock` is `root:docker` and the login user is not in the
    `docker` group, so the daemon is running but unreachable without root.
    (Distinct from BUG-005, where the engine itself was not running.)
- **Fix**
  - `sudo usermod -aG docker $USER`, then log out/in (or `newgrp docker`).
  - Until then, tests can be run on the host as a fallback: a venv with
    `backend/requirements-dev.txt` for pytest/ruff, `npm ci` in `frontend/`
    for Vitest/eslint - but `make test` in Docker remains the authoritative
    gate.

---

## BUG-006: ruff flags valid imports with I001 (first-party `app` not detected)

- **Symptoms**
  - `ruff check .` reported `I001 Import block is un-sorted or un-formatted`
    on files whose imports were correctly grouped (stdlib / third-party /
    `app.*`), including files that had previously passed lint.
- **Root cause**
  - `backend/pyproject.toml` had `src = ["app", "tests"]`. ruff resolves those
    relative to the project root, so it looked for first-party packages
    *inside* `backend/app/` and `backend/tests/`. The `app` package actually
    lives *at* the root, so `app` was classified third-party and its imports
    were expected in the third-party block.
- **Fix**
  - Set `src = ["."]` so ruff finds the `app` package and treats it as
    first-party. No import blocks needed reordering.

---

## BUG-001: Files saved as UTF-16 break Docker/YAML/Python builds

- **Symptoms**
  - `docker compose ...` failed with `yaml: control characters are not allowed`.
  - Docker build failed with `dockerfile parse error ...: unknown instruction:  F R O M`
    (letters separated by spaces).
  - Reading a file showed garbled/mojibake (CJK-looking) characters even though
    the build had previously worked.
- **Root cause**
  - On this Windows setup, the editor/file-writing tooling saves new/edited text
    files as **UTF-16LE** instead of UTF-8. Docker, YAML, and Python expect
    UTF-8; the extra null bytes appear as control characters or split tokens.
- **Fix**
  - Re-save the affected file(s) as **UTF-8 (no BOM)**. Quick check/convert
    (PowerShell): read bytes, if `bytes[1] == 0 && bytes[0] != 0` it is UTF-16 -
    decode as `Encoding.Unicode` and rewrite with `UTF8Encoding($false)`.
  - `.gitattributes` enforces `* text=auto eol=lf` to normalize on commit.
  - Prevention: after writing/editing a file with the assistant tooling, verify
    it is UTF-8 before running Docker/YAML/Python against it.

---

## BUG-002: Backend crash parsing BACKEND_CORS_ORIGINS

- **Symptoms**
  - Backend container exited on startup (compose e2e aborted).
  - Traceback ended with:
    `pydantic_settings.sources.SettingsError: error parsing value for field
    "backend_cors_origins" from source "EnvSettingsSource"`.
- **Root cause**
  - `backend_cors_origins` is typed as `list[str]`. pydantic-settings treats
    complex types as JSON and tries to `json.loads()` the env value **before**
    field validators run. Our value is a plain comma-separated string
    (`http://a,http://b`), which is not valid JSON, so parsing raised.
- **Fix**
  - Annotate the field with `NoDecode` so pydantic-settings skips JSON decoding
    and lets our `field_validator(mode="before")` split the comma string:
    `backend_cors_origins: Annotated[list[str], NoDecode] = [...]`.
  - Regression test: `backend/tests/unit/test_config.py`.

---

## BUG-003: E2E wait-on times out (health check returns 405)

- **Symptoms**
  - `e2e` container failed with `Error: Timed out waiting for:
    http://proxy/api/health`.
  - Backend logs showed repeated `"HEAD /api/health HTTP/1.1" 405 Method Not Allowed`.
- **Root cause**
  - `wait-on` probes `http://` URLs with an HTTP **HEAD** request by default, but
    the FastAPI health route only allows **GET**, so it returned 405 and wait-on
    never saw a success.
- **Fix**
  - Use the `http-get://` scheme so wait-on issues a GET. In `tests/e2e/Dockerfile`
    the health URL is rewritten from `http://` to `http-get://` before waiting.
  - Alternative: add HEAD support to the health route.

---

## BUG-004: `make help` fails under sh (git bash)

- **Symptoms**
  - Running `make help` in MINGW64/git bash printed:
    `` /usr/bin/sh: -c: line 1: syntax error near unexpected token `(' ``
    and `make: *** [Makefile:14: help] Error 2`.
  - Worked under Windows `cmd`, failed under `sh`.
- **Root cause**
  - Help recipe used `@echo ... (http://localhost)`. When make runs the recipe
    through `sh`, the unquoted `(` is a shell metacharacter and is a syntax error.
- **Fix**
  - Removed parentheses from the `echo` lines (e.g. `... at http://localhost`),
    keeping the help output shell-safe in both `sh` and `cmd`.
  - Prevention: avoid unquoted shell metacharacters `()`, `&`, `;`, `|`, `<`, `>`
    in Makefile `echo` recipes, or quote the whole string.

---

## BUG-005: Docker engine unreachable mid-session

- **Symptoms**
  - `docker ...` failed with
    `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.`
- **Root cause**
  - Docker Desktop's engine was not running (stopped/restarted).
- **Fix**
  - Start Docker Desktop and wait for the engine: poll `docker info` until it
    returns a server version, then retry the command.
