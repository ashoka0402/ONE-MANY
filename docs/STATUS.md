# Stage 2 — Implementation status

Current stage: **Stage 2 — AI Extraction & Opt-in Demand Matching — COMPLETE at the automated test/build level**. Stage 3 has not started.

## Implemented in source

- Gemini generateContent structured-output adapter (server-only GEMINI_API_KEY and configurable model/timeout); no heuristic substitution or fabricated successful output.
- Strict Pydantic extraction validation and request-text/model fingerprints for caching; text edits clear cached extraction.
- Explicit per-need discovery consent (false by default); no public read API for raw requests or other users' identities.
- Persisted `need_intents` and normalized `needs.location_key` with Alembic revision 20261112_02; existing Stage 1 location labels are backfilled without consent.
- Conservative matching by exact model-normalized asset, explicit consent, same self-reported area, different owner, feature constraints and non-overlapping complete date windows.
- Anonymous aggregate count API, documented feasibility caveats, client UI controls.
- Regression tests for privacy, date overlap, feature exclusions, missing/invalid provider response, and cache invalidation.
- CI: frontend lint/build, backend tests/Ruff, actual PostgreSQL migration and owner-scoped matching smoke — all passed in [run 43089572828](https://github.com/ashoka0402/ONE-MANY/actions/runs/43089572828). There are **28 passing backend tests** (Stage 1 and Stage 2 combined).

## Still pending

An actual Gemini request must be run by a user who has provisioned a valid API key; CI uses a deterministic provider fixture and does **not** verify third-party account credentials. Browser screenshots/interactions are not captured by CI. The temporary CI formatter was removed, and permanent verification uses read-only repository permissions. Product catalog, shopping groups, contributions, PayPal, Bryntum, AG Grid and deployment belong to later stages.

## Safety limitations

- Automated matches are **opportunities**, not confirmed viable products or safe schedules.
- Only an anonymized aggregate is returned; no other member's free text/IDs/emails.
- Ambiguous models can return unshareable, and synonymous asset descriptions can fail conservative exact matching.
- The system does not geocode neighborhoods. Missing dates require manual scheduling confirmation; overlapping full-day windows are excluded.
- The provider request sends the user's description only when they click Analyze. A configured key must be backend-only.
