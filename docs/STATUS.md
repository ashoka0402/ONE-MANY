# Stage 6 — AG Grid Community verified Sandbox contribution ledger

Status: **Implemented in source, automated verification pending final CI**. Live provider credentials and browser-level QA remain deferred.

## Implemented

- AG Grid Community 36.3.0 for authenticated member contributions and an append-only recorded event history; sort, filter, pagination and anonymized CSV export.
- A read-only `GET /api/v1/funding/groups/{id}/ledger` API requiring accepted membership. Other accounts receive a 404; pending or missing captures do not count as verified.
- Exact integer-minor-unit summary totals sourced from accepted `funding_members` plus previously server-verified `payment_attempts`; no new money records or PayPal network requests on GET.
- Statuses distinguish `in_progress`, `reconciled` and `requires_review` without treating a Sandbox approval redirect or pending attempt as completed.
- Append-only `funding_ledger_events` in Alembic revision `20261112_06`, keyed to prevent retry-driven duplicates. Events originate from group creation, joins, order creation, capture request, server-verified capture and signed webhook changes.
- Event records expose only anonymous participant slots and server-recorded timestamps; sensitive PayPal IDs, payer emails, raw needs and tokens are excluded.
- Existing Stage 1–5 API behavior, scheduling and payment endpoints remain in place.

## Trust boundaries

This is a **PayPal Sandbox test-merchant** ledger, not real money, escrow, bank settlement or proof of retailer acquisition. The ledger records prior verification rather than calling PayPal on every page view; past state changes before the Stage 6 audit migration are not invented. A refund/denial event can invalidate a previously completed member contribution and force review. Provider fixtures are test-only.

## Automated and manual checks

The Stage 6 CI run verifies React build, Python tests, Ruff, a live PostgreSQL migration and owner-scoped ledger smoke. Browser-level visual inspection and live PayPal/Gemini/Channel3 credential verification remain on the final manual checklist.
