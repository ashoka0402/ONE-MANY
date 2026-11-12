# ONE / MANY

**Many people. One smarter purchase.**

ONE / MANY helps people discover compatible requests and propose shared purchases. Stage 3 integrates **real Channel3 product searches and offer rechecks** with persistent, deterministic draft cost-sharing quotes. There is no PayPal charge or physical purchase in this stage.

## What is actually implemented

- Stage 1: registered accounts, password hashing, private PostgreSQL needs and API ownership checks.
- Stage 2: opt-in anonymous matching, real Gemini structured extraction and conservative feature/date/area gates.
- Stage 3: **Channel3 REST API** with server-only API key, search and product detail lookup, real normalized merchant offers, valid in-stock currency/price filtering, quote snapshots based on potential matches, exact minor-unit allocation, and authenticated draft history.
- Browser workspace: click Analyze, opt in, Find potential matches, Find products, select an in-stock merchant offer, Save draft quote, Load saved drafts.
- If Channel3 or Gemini credentials are missing, the corresponding endpoint returns 503. Neither provider has a hardcoded production fallback.

[Status](docs/STATUS.md) · [Architecture](docs/ARCHITECTURE.md) · [Integration contracts](docs/INTEGRATION_CONTRACTS.md) · [Roadmap](docs/ROADMAP.md)

## Setup

Use Node 22.12+, Python 3.12+, Docker Compose and PostgreSQL. From repository root, set up the DB:

```powershell
Copy-Item .env.example .env
# Configure a unique POSTGRES_PASSWORD in root .env.
docker compose up -d --wait postgres
```

From `apps/api`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Configure DATABASE_URL, AUTH_SECRET, GEMINI_API_KEY, CHANNEL3_API_KEY
# Never commit apps/api/.env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --host 127.0.0.1 --port 8000
```

Set `CHANNEL3_COUNTRY=US` and `CHANNEL3_CURRENCY=USD` for the default demo, or use a supported country/currency pair. The API rejects mismatched currencies in offers and does not perform FX conversion. Channel3 developer account: https://trychannel3.com/developers.

In another terminal, from repository root:

```powershell
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Visit http://localhost:3000/app. To draft a shared purchase, create two accounts with different nonoverlapping date windows in the same self-reported area, opt into discovery for both needs, and analyze them. On the first account, Find potential matches, Find products, then choose an eligible Channel3 offer and Save draft quote.

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

GitHub CI tests the provider HTTP contract using mocks (not fake production responses), validates the PostgreSQL migration and builds an authenticated, persisted quote against a deterministic test fixture.

## Safety and scope

Quotes are **draft price snapshots**, not verified local shipping costs, investments, escrow, binding group commitments, actual savings, or payment requests. Participants in a quote are derived from compatible opted-in *potential* members and have **not accepted or funded anything**. Hypothetical savings assume each person otherwise would have bought the exact same product. Offers, availability, taxes, shipping, ownership agreements and costs must be rechecked before any real payment. Stage 4 will use PayPal Sandbox only.

[MIT License](LICENSE).
