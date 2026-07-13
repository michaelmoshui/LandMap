# BUG_LOG.md

A running log of bugs encountered in LandMap and how they were resolved. Newest
first. **Before debugging a new issue, scan this file for related symptoms.**

Each entry records:
- **Symptoms** - what was observed (error text, behavior).
- **Root cause** - the underlying reason.
- **Fix** - what resolved it (and how to avoid it).

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
