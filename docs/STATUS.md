# Stage 4 — PayPal Sandbox funding and reconciliation

**Stage 4 complete at the automated build/test level.** The PayPal Sandbox API and browser redirect have not been exercised with real credentials.

## Implemented

- Persisted, time-limited funding groups, hashed invitations, owner-linked memberships and single-attempt payment ledgers through Alembic revision `20261112_04`.
- Explicit member acceptance and compatibility checks before any order. Potential AI matches are not charged or automatically joined.
- Real PayPal Sandbox OAuth + Orders v2 API adapter, fixed server-owned amounts, stable create/capture idempotency keys, order and completed-capture verification.
- Server-side signature verification for PayPal webhooks and deduplication by verified event ID. Refund/denial events mark the group for review and remove reversed captures from the completed total.
- UI for invitations, joining, PayPal approval and post-redirect reconciliation.
- Tests with provider mocks confined to test code, covering ownership, amount mismatches, duplicate attempts, consent withdrawal and webhook replay.

## Still pending

GitHub Actions [run 43161652139](https://github.com/ashoka0402/ONE-MANY/actions/runs/43161652139) passed: **41 backend tests**, Ruff, Next.js ESLint/TypeScript/production build, PostgreSQL migration `20261112_04`, a live PostgreSQL recruitment and persisted PayPal order-attempt smoke test, and Docker Compose configuration. Live Gemini/Channel3/PayPal credentials, buyer approval, browser redirect and HTTPS webhook tests remain intentionally deferred to final manual QA. Provider responses are fixtures only inside tests.

## Boundaries

Sandbox payments are fake merchant payments, not escrow, shared legal ownership, authorized retailer purchase or a guarantee of a refund. Only server-verified completed captures count. No real-money mode exists.
