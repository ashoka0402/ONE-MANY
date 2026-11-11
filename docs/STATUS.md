# Status

Current stage: **0 — Foundation and design system**. Updated: **November 12, 2026 (IST)**. Stage 1 has not started.

## Implemented scope

- Two-service monorepo with Next.js App Router frontend and FastAPI backend.
- ONE / MANY landing page and application shell with explicitly future-stage empty states.
- Brand palette, responsive design tokens, shared UI components and reduced-motion-aware decoration.
- Public `/api/v1/health` liveness endpoint, environment settings, centralized safe error bodies, JSON application/server error logging and explicit local CORS policy.
- PostgreSQL connection configuration, SQLAlchemy/Alembic dependencies, and loopback-only PostgreSQL Docker Compose service with persistent volume.
- Environment templates, ignore rules, architecture, decisions, roadmap, integration contracts and agent handoff instructions.

## Missing by design

No authentication, user data, business schema, migrations, matching, AI requests, product retrieval, checkout, verified contributions, scheduling, ownership ledger, or deployment. The landing example is illustrative. No feature is represented as a successful live transaction or AI result.

## Commands

Follow the one-time installation and environment instructions in [README](../README.md).

| Purpose | Command | Directory |
| --- | --- | --- |
| Web development | `npm run dev:web` | Repository root |
| API development | `.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log` | `apps/api` |
| PostgreSQL | `docker compose up -d postgres` | Root, after configuring `.env` |
| Frontend lint | `npm run lint:web` | Root |
| TypeScript | `npm run typecheck:web` | Root |
| Production build | `npm run build:web` | Root |
| Backend tests | `.\.venv\Scripts\python.exe -m pytest -q` | `apps/api` |
| Backend lint | `.\.venv\Scripts\python.exe -m ruff check .` | `apps/api` |
| Compose validation | `docker compose config --quiet` | Root, with password configured |

## Latest verification

Verification is in progress; this section must be replaced with final measured results before the Stage 0 checkpoint.

- Node 22.23.2, npm 10.9.8 and Python 3.13.14 are available and meet the minimum versions.
- Docker Compose v5.1.4 configuration validation passed using a process-local dummy validation password; no real credentials were written.
- Docker CLI is installed, but its engine is unavailable: `dockerDesktopLinuxEngine` named pipe was not found. PostgreSQL startup, readiness and live connection cannot be verified in this environment until Docker Desktop/Engine is running.

## Known limitations and next-stage cautions

- Health reports process liveness only. Do not use it as database/provider readiness.
- Access logging must remain disabled or be explicitly redacted when sensitive query parameters are introduced. Application/server error logs intentionally omit traceback details; use safe event metadata for diagnostics.
- CORS is GET-only, has no credential support, and defaults to `http://localhost:3000`; extend intentionally with authenticated mutation endpoints and tests in a later stage.
- PostgreSQL runtime is unverified because the Docker engine is stopped. Its named volume persists across stops; never remove it casually.
- Future Bryntum and AG Grid features require license review; no paid components are included.
- No production deployment or payment/security certification is implied.
