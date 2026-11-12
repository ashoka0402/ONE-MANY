# ONE / MANY

**Many people. One smarter purchase.**

ONE / MANY helps people discover compatible requests and propose shared purchases. Stage 3 integrates **real Channel3 product searches and offer rechecks** with persistent, deterministic draft cost-sharing quotes. There is no PayPal charge or physical purchase in this stage.

## Stage 4: PayPal Sandbox funding

Stage 4 adds member-approved **Sandbox-only** checkout to the existing Gemini + Channel3 workflow. A potential AI match does not enroll or charge anybody.

1. The organizer creates a funding group from a fresh Stage 3 catalog draft. The backend rechecks the selected merchant price.
2. The organizer shares an invitation code. A second account explicitly joins using its own compatible, opted-in need, with a non-overlapping date window.
3. After all slots are accepted, each participant chooses PayPal Sandbox approval for **their own exact share**. The server rechecks eligibility and the live Channel3 offer.
4. PayPal redirects back to the app. Because access tokens are memory-only, sign in again, refresh the group list and click **Verify / capture approved payment**.
5. The backend fetches the PayPal order, checks reference IDs, exact amount and currency, performs idempotent capture when approved, then checks PayPal again. Only a verified COMPLETED capture increases the ledger.
6. The group is funded only if every accepted participant has a verified capture and the total matches the quote. Verified signed webhook events also reconcile completion and reversals.

**Important:** Sandbox payments use fake money. Funds go to the test merchant account, **not escrow**; no retailer purchase, automatic refunds, asset delivery, or legal co-ownership is implemented.

### Deferred credentials

Add these **server-only** values to `apps/api/.env` during final manual QA, not to GitHub:

```dotenv
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_WEBHOOK_ID=your_sandbox_webhook_id
PUBLIC_WEB_URL=http://localhost:3000
```

A webhook listener must be publicly accessible via HTTPS to receive PayPal events; register `POST /api/v1/paypal/webhook` in the Sandbox app for capture completed, pending, denied and refunded notifications. The adapter has **no production PayPal URL**. PayPal Orders v2 does not support INR as an ordinary Checkout currency, so the app rejects INR funding groups rather than silently converting amounts.

Apply the new migration: `cd apps/api && python -m alembic upgrade head`. The rest of the Stage 3 setup and test commands below remain applicable.

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
