# ONE / MANY

**Many people. One smarter purchase.**

ONE / MANY is an AI-assisted shared-asset purchasing and scheduling prototype. People independently describe needs; Gemini identifies potentially reusable assets, the backend finds compatible opted-in requests, Channel3 supplies live product candidates, and PayPal **Sandbox** demonstrates independently authorized contributions. Bryntum Scheduler Community displays persisted, non-overlapping provisional usage reservations. AG Grid Community shows the authoritative server-recorded Sandbox contribution snapshot and audit history.

## Implemented

| Stage | Feature | Backend source of truth |
| --- | --- | --- |
| 0 | Next.js/FastAPI, PostgreSQL, CI, responsive branding | GitHub Actions |
| 1 | User accounts, private needs CRUD | PostgreSQL and JWT authentication |
| 2 | Real Gemini structured extraction, anonymous opt-in matches | Strict Pydantic validation and matching constraints |
| 3 | Real Channel3 product lookup, in-stock offer recheck, accurate draft shares | Channel3 product/offer API + exact minor-unit arithmetic |
| 4 | Explicitly joined funding groups, PayPal Orders v2 Sandbox, verified capture ledger and signed webhook handling | PayPal Sandbox and PostgreSQL |
| 5 | Bryntum Scheduler Community, authorized member reservations, edit/cancel, DB-level conflict prevention | PostgreSQL GiST exclusion constraint |
| 6 | AG Grid Community contribution ledger, verified-capture totals, member-anonymous CSV exports and append-only audit events | PostgreSQL funding and payment records |

**Scope:** This is a hackathon prototype. PayPal Sandbox uses fake money; no real retailer order, escrow, legal shared ownership, automatic refund, verified physical handover or shipping is performed. All reservations are *provisional usage plans* rather than real-world inventory commitments.

## Run locally

Requirements: Node.js 22.12+, Python 3.12+, Docker Compose and a local PostgreSQL 17 service.

```powershell
# From repo root
Copy-Item .env.example .env
# Set POSTGRES_PASSWORD in .env
docker compose up -d --wait postgres

# In API directory
cd apps/api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
# Set DATABASE_URL and a strong, unique AUTH_SECRET
# For live integrations also set GEMINI_API_KEY and CHANNEL3_API_KEY
# For Sandbox integration set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET
# For deployed redirect set PUBLIC_WEB_URL to the HTTPS application origin
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn one_many_api.main:app --reload --port 8000
```

Start the Next.js frontend in a second terminal, from the repo root:

```powershell
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Open http://localhost:3000/app. The API Swagger UI is at http://localhost:8000/docs.

## Intended application flow

1. Register separate users. Each creates a natural-language need with an explicitly opted-in area and **complete, non-overlapping** required date range.
2. Each user clicks **Analyze with Gemini**. AI extraction is sent to the configured external provider only on that action; no fake fallback exists.
3. Discover matching needs in the same normalized area, then query Channel3 for real asset candidates and actual merchant offers.
4. Save a draft quote. The amount comes from Channel3, and shares are computed by deterministic integer arithmetic.
5. Create a funding group. Each prospective participant **explicitly** joins using an authenticated compatible need and invitation.
6. Everyone approves their own share through PayPal Sandbox. Re-authenticate after returning to the app and use **Verify/capture**. The server checks PayPal's order and completed capture before counting it.
7. When every contribution is independently verified, load the **Shared-use calendar**. Choose a group, check your allowed need window and save your provisional whole-day reservation.
8. Other group members can see anonymous booking slots and reserve only their own available days. They cannot edit or cancel another member's reservation. All writes are validated by the backend and PostgreSQL's overlap exclusion constraint.
9. Open the **Contribution ledger**. Select an accepted group to inspect accepted shares, server-recorded completed Sandbox captures, outstanding amount, and read-only audit history. You can sort/filter/export anonymous rows with AG Grid.

## Scheduling model

Stage 5 retains **inclusive whole-day civil dates** from the existing needs schema. Bryntum receives each booking as a start date plus the exclusive day *after* the last date, consistent with its timeline event model. There are no timestamps or silently inferred IANA time zones. Adjacent days are allowed; sharing within a day, shipping time, travel and handover buffers are **not** modeled. An owner can have at most one active reservation per funding group. A group marked `needs_review` cannot add or change bookings, but existing plans remain visible to its members and can be cancelled.

An application group must be `funded` with **all** matching completed Sandbox capture records before reservations may be created. All accepted members have separate needs. PostgreSQL serializes scheduling mutations via a row lock on the group and rejects overlapping active dates independently using a GiST exclusion constraint. A version number prevents stale scheduling edits. The frontend is intentionally read-only: form changes are sent to FastAPI, never directly edited in Bryntum's event store.

### AG Grid contribution ledger

Stage 6 integrates `ag-grid-react` and `ag-grid-community`, pinned to version 36.3.0 (MIT Community edition). Both the participant table and recorded-event table provide client-side sorting, filtering, pagination and anonymous CSV export. No Enterprise component, license key, browser-side payment mutation or fabricated financial data is present.

`GET /api/v1/funding/groups/{id}/ledger` is read-only and requires membership. It calculates verified captured totals **only** from stored completed attempts with a PayPal capture ID and a matching accepted share/currency. Pending, reversed, inconsistent and never-started attempts contribute exactly zero. Anomalous or reversed groups are marked `requires_review` rather than quietly marked funded. The append-only `funding_ledger_events` table records real application state transitions and verified webhook observations with idempotency keys. The history starts with Stage 6; older payments have no invented backfill. Neither the API nor the CSV export reveals another participant's identity, PayPal order/capture IDs or credentials.

The ledger is a **snapshot** of prior server-verified Sandbox events, not a fresh PayPal financial reconciliation or independently confirmed bank settlement. Do not present test-merchant captures as real funds or escrow.

### Bryntum licensing

Uses `@bryntum/scheduler-community` and `@bryntum/scheduler-react-community`, pinned at **8.0.0** from the public npm registry. The Community tier is **MIT-licensed and free**; it does **not require an API key or paid license**. See [Bryntum's official tiers FAQ](https://bryntum.com/tiers-faq/) and [React integration guide](https://www.bryntum.com/docs/guide/Scheduler/integration/react/guide). It is rendered via a client-only dynamic Next.js import, with one structural CSS file and one light theme.

## Automated validation

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
cd apps/api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m alembic current
```

GitHub Actions additionally applies migrations on PostgreSQL, exercises actual authenticated funding/reservation writes, and deliberately attempts an overlapping database insertion to prove the GiST constraint rejects it. AI, Channel3 and PayPal use explicit **test-only** mocks in automated tests; production never returns fake successful provider results.

Live integration keys, PayPal buyer redirects, local/deployed browser screenshots and accessibility checks are deferred to the final manual QA pass. See [Manual QA checklist](docs/MANUAL_QA.md).

[Architecture](docs/ARCHITECTURE.md) · [API contracts](docs/INTEGRATION_CONTRACTS.md) · [Roadmap](docs/ROADMAP.md) · [MIT project license](LICENSE).
