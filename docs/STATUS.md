# Stage 3 — Product discovery and draft proposals

Status: **Stage 3 complete at the automated build/test level**. Stage 4 has not started.

## Added
- Real Channel3 search (`POST /v1/search`) for the Gemini-extracted reusable asset and stated required features.
- Server-side product revalidation (`GET /v1/products/{id}`) when the user selects an offer and asks for a draft quote.
- In-stock merchant offer normalization: HTTPS links, actual prices, supported currencies, no fabricated stock, no automatic currency conversion.
- Conservative catalog evidence labels: blocked, manual review, or candidate. Search text is not proof of physical suitability.
- Strict server-side pricing: integer minor units, exact shares with remainder, user-submitted prices ignored.
- Persistent `purchase_proposals` draft records in Alembic revision 20261112_03, owner-specific list/read API.
- Frontend product browser, merchant selector, unapproved quote breakdown and saved history.

## Still pending
- Live provider key/manual request verification and browser QA are deferred to final validation.
- No PayPal capture, buyer authorization, legal ownership contract, asset handover, verified location, shipping/taxes or member commitments. Sponsor dashboards and scheduling are later stages.

## Testing
- Stage 2 last fully verified: [GitHub Actions run 43089960294](https://github.com/ashoka0402/ONE-MANY/actions/runs/43089960294).
- Stage 3 checks passed in [GitHub Actions run 43157650820](https://github.com/ashoka0402/ONE-MANY/actions/runs/43157650820): 34 backend tests, Ruff, Next.js lint/typecheck/build, Alembic revision 20261112_03, a PostgreSQL-backed draft quote smoke test and Compose validation. After the final hardening, permanent CI runs without write access or autoformat steps. Live Channel3 credentials and actual merchant availability were not tested.
