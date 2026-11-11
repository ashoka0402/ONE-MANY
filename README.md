# ONE / MANY

**Many people. One smarter purchase.**

ONE / MANY is an AI-powered shared-ownership prototype. Stage 2 implements **opt-in, anonymous demand discovery** backed by a real Gemini structured-output adapter and conservative, deterministic matching rules. It does **not** buy products, coordinate reservations, or collect PayPal payments yet.

## Implemented now

- Account authentication and persisted private needs (Stage 1).
- Analyze a need with Gemini and store validated structured intent on the backend. Extraction is **not** hardcoded, and failed/unconfigured provider calls never create fabricated results.
- Explicit per-need permission to include it in neighborhood discovery; private by default.
- Compare only consented, open needs from different accounts with the same AI-normalized reusable asset label and self-reported area; reject explicit feature contradictions and overlapping known dates.
- Return anonymous match counts and scheduling uncertainty, not other users' names, raw requests, IDs, or email addresses.

[Current status](docs/STATUS.md) · [Roadmap](docs/ROADMAP.md) · [Architecture](docs/ARCHITECTURE.md) · [API contracts](docs/INTEGRATION_CONTRACTS.md) · [Decisions](docs/DECISIONS.md)

## Requirements

- Node.js 22.12+ and npm
- Python 3.12+
- PostgreSQL 17 via Docker Compose
- A **real Gemini API key** (server-side only) for live analysis. Without it, account management continues to work but analysis returns 503. No invented fallback is used.

## Local setup (PowerShell)

From the repository root:

```powershell
Copy-Item .env.example .env
# Choose a strong local POSTGRES_PASSWORD in the root .env
docker compose up -d --wait postgres
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Set DATABASE_URL to match the root password (URL-encode special characters)
# Generate AUTH_SECRET: python -c "import secrets; print(secrets.token_urlsafe(48))"
# Set GEMINI_API_KEY in apps/api/.env using your own Google AI Studio key.
# GEMINI_MODEL defaults to gemini-2.5-flash (change if your account uses another supported model)
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Start the frontend from a second terminal in the root directory:

```powershell
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Open http://localhost:3000/app. Register a user, create a need, optionally enable anonymous discovery, click **Analyze with Gemini**, and then **Find potential matches**. To observe a real match, register a second user with a compatible asset request and the same area label, enable discovery on that need, and analyze it. Use two different time windows to avoid a date conflict.

No API key is committed to GitHub or included in browser bundles. Only clicking Analyze sends that request text to the configured AI provider. There are no scripted, hardcoded demo matching responses in the application.

## Checks

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
cd apps/api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m alembic current
```

GitHub Actions validates all of the above except a real Gemini API request (which requires a private API key); it also runs the migrations against PostgreSQL and exercises authenticated, database-backed matching with a **test-only** deterministic AI fixture.

## API

Open http://localhost:8000/docs. Stage 1 authentication and owned-needs endpoints remain intact.

- `POST /api/v1/needs/{id}/analyze` — authenticated, owner-only; calls Gemini and caches by request text/model.
- `GET /api/v1/needs/{id}/matches` — authenticated, owner-only; requires discoverable/open/AI-analyzed/shareable need with an area. Returns only aggregate anonymized counts.
- `PATCH /api/v1/needs/{id}` supports `{"discoverable":true}` or `{"discoverable":false}` and invalidates the AI cache if the request description changes.
- `POST /api/v1/needs` accepts `"discoverable":true|false`; omitted defaults to **false**.

**Limitations:** Asset labels are model-generated and exact-match normalized, not embedding-based. Equivalent synonyms may be missed; the system deliberately favors precision over ungrounded matches. Area labels are normalized but **not geocoded**, so a matching label does not verify physical proximity. Overlapping whole-day windows are excluded; missing dates leave scheduling unresolved. No product catalog, pricing, ownership agreement or confirmed compatibility has been established. Consent and account controls are appropriate for a prototype, not a production marketplace.

MIT licensed: [LICENSE](LICENSE).
