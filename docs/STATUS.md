# Stage 6 — AG Grid Community verified Sandbox contribution ledger

Status: **Stage 6 complete at the automated build/test level**. Live provider credentials and browser-level QA remain deferred.

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

Stage 6's integration run [43167136166](https://github.com/ashoka0402/ONE-MANY/actions/runs/43167136166) passed React lint/typecheck and production build, Alembic revision `20261112_06`, a PostgreSQL-backed member-only ledger smoke and **50 backend tests**, but initially failed Ruff import order. The import has been fixed, the temporary npm lockfile step removed, and the permanent workflow now uses read-only permissions. Final verification is the subsequent clean CI run. Browser-level inspection and live PayPal/Gemini/Channel3 credential tests remain on the manual checklist.
