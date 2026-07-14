# CLAUDE.md

Guidance for Claude Code working in this repository.

The operating guide for AI agents on LandMap lives in **`AGENTS.md`** (rules,
architecture, golden rules, definition of done) and **`SKILL.md`** (task
playbooks). Read both before non-trivial changes. They are the source of truth;
this file only imports them so they load automatically.

@AGENTS.md
@SKILL.md

## Claude-specific notes

- When debugging, scan **`BUG_LOG.md`** first (recurring issues are documented),
  and add a new entry for any novel bug you fix. See the workflow in `AGENTS.md`.
- Everything runs in Docker via `make` targets — do **not** assume host-installed
  Python or Node. Run `make lint` and `make test` before declaring work done.
- Common permissions are pre-approved in `.claude/settings.json`, so `make`,
  `docker compose`, and read-only `git` commands run without prompting.
