# ONE / MANY

**Many people. One smarter purchase.**

A community-first collective purchasing prototype: Stage 1 now includes **real accounts and a private, persistent needs workspace**, while AI demand matching, Channel3, PayPal payments, AG Grid, and Bryntum scheduling are upcoming stages. No purchases or live payment capabilities are claimed.

[Development status](docs/STATUS.md) · [Roadmap](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md) · [API contracts](docs/INTEGRATION_CONTRACTS.md) · [Decisions](docs/DECISIONS.md)

## Requirements

- Node.js 22.12+ and npm
- Python 3.12+
- Docker Engine/Desktop and Docker Compose

## Start PostgreSQL (required for Stage 1)

From repository root (PowerShell):

```powershell
Copy-Item .env.example .env
# Replace POSTGRES_PASSWORD in the root .env with a unique local password.
docker compose up -d --wait postgres
```

## Start API and migrate database

```powershell
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Set DATABASE_URL to match the root .env (URL-encode special chars).
# Generate a random AUTH_SECRET of >=32 characters, then add it to apps/api/.env.
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

For macOS/Linux, use `.venv/bin/python` and `cp`. Start the API from `apps/api` so Pydantic loads that directory's `.env`. API docs: http://localhost:8000/docs; liveness: http://localhost:8000/api/v1/health.

## Start the Next.js frontend

In a separate PowerShell terminal, from repository root:

```powershell
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Visit http://localhost:3000 and then http://localhost:3000/app. Register, describe an item you need, edit it, archive it, and sign in again to see the persisted results.

## Test

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web

cd apps/api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m alembic current
```

GitHub Actions also checks a live PostgreSQL migration and API create/read smoke test. See the latest [CI runs](https://github.com/ashoka0402/ONE-MANY/actions).

## Stage 1 API endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/needs`
- `GET /api/v1/needs?limit=30&offset=0&status=open`
- `GET /api/v1/needs/{id}`
- `PATCH /api/v1/needs/{id}`
- `DELETE /api/v1/needs/{id}` (archives; not permanent deletion)

All needs endpoints require `Authorization: Bearer <token>`. The only public API routes beyond docs and health are account creation and login. Tokens expire after one hour by default; the demo web app retains them in memory only, so refreshing requires logging in again.

**Security note:** CORS is not authentication. All need reads and mutations check ownership server-side. Do not expose real credentials, seed fake payment data, or imply escrow. Stage 1 is a hackathon prototype, not a production-ready consumer identity platform.

MIT licensed: [LICENSE](LICENSE).
