# Stage 4 — PayPal Sandbox funding and reconciliation

**Implementation committed; automated verification pending.**

## Implemented

- Persisted, time-limited funding groups, hashed invitations, owner-linked memberships and single-attempt payment ledgers through Alembic revision `20261112_04`.
- Explicit member acceptance and compatibility checks before any order. Potential AI matches are not charged or automatically joined.
- Real PayPal Sandbox OAuth + Orders v2 API adapter, fixed server-owned amounts, stable create/capture idempotency keys, order and completed-capture verification.
- Server-side signature verification for PayPal webhooks and deduplication by verified event ID. Refund/denial events mark the group for review and remove reversed captures from the completed total.
- UI for invitations, joining, PayPal approval and post-redirect reconciliation.
- Tests with provider mocks confined to test code, covering ownership, amount mismatches, duplicate attempts, consent withdrawal and webhook replay.

## Still pending

CI must pass Stage 4 frontend, Python tests, PostgreSQL migration and funding smoke checks. Real Gemini, Channel3 and PayPal Sandbox credentials, actual browser redirects and HTTPS webhooks remain in the final manual QA pass.

## Boundaries

Sandbox payments are fake merchant payments, not escrow, shared legal ownership, authorized retailer purchase or a guarantee of a refund. Only server-verified completed captures count. No real-money mode exists.
