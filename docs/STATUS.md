# Stage 3 — Product discovery and draft proposals

Status: **Implemented in source; verify via latest GitHub Actions run before calling fully green**.

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
- Stage 3 tests and migration/quote smoke will run through GitHub Actions. Fixtures represent network/provider responses in tests only, not production data.
