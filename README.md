# ONE / MANY

**Many people. One smarter purchase.**

Stage 0 provides a premium responsive landing page, an honest application shell, and a FastAPI service foundation. Matching, products, payments, and scheduling are future work. No AI calls or financial transactions occur.

Read [current status](docs/STATUS.md), [roadmap](docs/ROADMAP.md), [architecture](docs/ARCHITECTURE.md), [decisions](docs/DECISIONS.md), and [integration contracts](docs/INTEGRATION_CONTRACTS.md) before continuing development.

## Prerequisites

- Node.js **22.12+** and npm (verified with Node 22.23.2; [.nvmrc](.nvmrc) pins that version).
- Python **3.12+** (verified with Python 3.13.14).
- Docker Engine/Desktop and Docker Compose for local PostgreSQL. The web and liveness endpoint can run without it.

## Start the frontend

From the repository root:

```powershell
npm --prefix apps/web ci
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Open <http://localhost:3000> for the landing page and <http://localhost:3000/app> for the application shell. The shell does not yet call the API. The public API origin in the web environment is configuration for later integration, never a place for secrets.

## Start the API

In another PowerShell terminal:

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Open <http://localhost:8000/api/v1/health> or API docs at <http://localhost:8000/docs>. Run from `apps/api` so settings load its `.env`. On macOS/Linux use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`, and `cp` in place of `Copy-Item`.

Application and Uvicorn server error logs use JSON and omit exception values and tracebacks after application initialization. Access logging is disabled in the documented command to avoid logging sensitive query strings. Health is **liveness only**, not database readiness.

## Start PostgreSQL (optional for Stage 0)

From the repository root:

```powershell
Copy-Item .env.example .env
# Edit .env and set a unique POSTGRES_PASSWORD, then:
docker compose up -d postgres
docker compose ps
```

Set `DATABASE_URL` in `apps/api/.env` to `postgresql+psycopg://one_many:<URL-encoded-password>@localhost:5432/one_many`, matching the root `.env`. The password must be URL-encoded if it contains special characters. Stage 0 validates connection configuration without opening a connection or creating tables. Do not commit either local environment file.

PostgreSQL binds to `127.0.0.1:5432` and persists in a named Docker volume. `docker compose down` stops it while preserving data. Changing `.env` credentials after a volume is initialized does not change the database role's password; migrate credentials deliberately and do not delete volumes to work around it.

## Verify

```powershell
# Repository root
npm run lint:web
npm run typecheck:web
npm run build:web
docker compose config --quiet

# apps/api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Compose validation requires a configured root `.env`. See [STATUS](docs/STATUS.md) for actual results and limitations. Production web serving after a successful build: `npm --prefix apps/web start`.

## Layout

```text
apps/
  web/                 Next.js App Router, UI, design tokens, npm lockfile
  api/                 FastAPI, settings, logging, tests, Python dependencies
docs/                  Architecture, roadmap, status, decisions, contracts
docker-compose.yml     Local PostgreSQL only
.env.example           Database environment template
AGENTS.md              Rules for future stages and agents
```

Do not start Stage 1 until explicitly requested. No deployment is included.
