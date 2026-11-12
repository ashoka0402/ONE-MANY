# Decisions

## Stage 0: keep two services and simple commands

Use a small monorepo with independent npm and Python dependency management. Root npm scripts forward to the web package; no monorepo task runner or extra orchestration framework is needed. Node >=22.12 satisfies the stated Flute compatibility requirement; Flute itself is not required or installed. Python >=3.12 is required.

## Use stable, explicit boundaries

FastAPI owns `/api/v1`. Health is liveness, not a promise that PostgreSQL or a future external provider is available. Environment settings configure the database; Stage 0 needs no schema, migration, or request-time database session. SQLAlchemy, Alembic, and the PostgreSQL driver are prepared for the persistence stage.

## Design around an honest product preview

Charcoal `#11191A`, warm white `#F7F8F4`, lime `#B8F26A`, lavender `#A89CDB`, and gray-green surfaces form the identity. Editorial hierarchy, borders, whitespace, and deliberate cards carry the design. Lightweight decorative motion respects reduced-motion preferences. Product examples are illustrative; the app shell never invents people, transactions, completed funding, or AI results.

Use shadcn/ui and official-registry Aceternity source components rather than undocumented APIs. Record installed component provenance in the web package. Keep local modifications scoped to accessibility and the brand. No image-generation service or paid assets are necessary for this foundation.

## Local PostgreSQL requires explicit configuration

Compose uses PostgreSQL 17 and a named volume, binds only to `127.0.0.1`, and requires a local password from the ignored root `.env`. The example deliberately leaves it empty. API connection configuration must match it; URL-encode special characters in the database URL. Do not log URLs or credentials. Runtime database verification requires a running Docker engine.

## Deferred functionality

Authentication, business models, migrations, AI calls/matching, Channel3, PayPal, Bryntum, AG Grid, purchases, ledger records, and deployment are deferred. Provider contracts remain planning notes until implementation and provider verification. Commercial integration licensing will be decided before using paid functionality. There is no production security or payment-readiness claim for Stage 0.

## Stage 0 recovery — interrupted Codex run

Restore required tsParticles, Motion and Tailwind PostCSS packages; use the official Aceternity Bento Grid example adapted for the existing design system. Keep the Next.js links as semantic links rather than using Base UI Button's unsupported `asChild` syntax. Import brand.css after Tailwind globals. Add a CI workflow to regenerate the dependency lockfile once in GitHub Actions, then validate frontend, backend and Compose. Local npm registry and Docker are unavailable in the editing environment; any unrun check must remain explicitly unverified until CI confirms it.

The one-time CI lockfile repair succeeded. The verification workflow now operates with read-only repository permission and validates the committed lockfile with npm ci. It also probes a real PostgreSQL instance on the GitHub runner; consult the latest workflow status for runtime verification.

## Stage 1 — Identity and persistence

Persist only users and need requests in this stage. Product matching, contributions and reservations require later migrations to avoid speculative financial schemas. Use UUIDs and server-owned foreign keys. Normalize email on input and enforce uniqueness in DB. Hash passwords with Argon2; sign 60-minute tokens with a server-only random AUTH_SECRET (at least 32 characters) and explicit algorithm/issuer/audience claims. Production configuration must require credentials.

The web app holds the short-lived token in React memory only: no localStorage, sessionStorage or insecure cookie persistence. Refresh requires re-login; intended as a defensible hackathon compromise, not a production account architecture. Ownership is asserted in every database query; never fetch a record and rely only on a frontend guard. Archive instead of permanently deleting needs. Maintain deterministic validation for date windows. Use Alembic to manage real Postgres migrations; SQLite in-memory tests provide quick isolation regressions while CI validates a live PostgreSQL migration and API write/read sequence.

Stage 1 verification succeeded against live PostgreSQL and an authenticated write/read smoke test. A one-time CI formatting operation committed Ruff-compliant Python sources; permanent CI retains read-only permissions and does not mutate the repository. Manual browser QA and deployment remain outside Stage 1.

## Stage 2 — Model does interpretation; backend owns admission to discovery

Use Gemini generateContent with a constrained JSON schema, strict Pydantic validation, explicit provider timeouts, and no fake fallback if the key is missing/invalid. Provider model name and key are configurable; do not hardcode a specific example result as runtime behavior. Real input is sent only when the signed-in owner clicks Analyze. Cached successful extractions are keyed to description+model and cleared on description change.

A need is private by default (discoverable=false), including all Stage 1 migrated needs. Discovery requires explicit per-need opt-in, open status, usable location label, and valid shareable extraction. Return only member counts and scheduling uncertainty, not peer personal data or raw text. Require exact normalized self-reported area and canonical asset label, reject explicit feature contradictions and overlapping known date windows; missing date windows are unconfirmed. This knowingly trades recall for reliability until a richer canonical product ontology and geocoding are available.

Asynchronous/background workers, catalog data, group creation, pricing and payment states are intentionally deferred. The provider call is synchronous with a bounded timeout. The UI shows failed/unconfigured provider calls clearly; do not turn errors into pretend successful AI. Strict terms and semantic safety are not guaranteed by LLM output; real product suitability requires Stage 3 verification.

Stage 2 verification passed in GitHub Actions run 43089572828, including 28 Python tests and a live PostgreSQL migration and anonymized matching smoke. The one-time code formatter has been removed from permanent CI; check-only jobs use read-only permissions. Live Gemini credentials and visual browser QA were not available in CI and must not be reported as tested.


## Stage 3 — Authentic catalogue offers and strictly hypothetical cost allocation

Use Channel3's official REST contract directly, with `x-api-key` in the FastAPI backend only. `POST /v1/search` returns product candidates; `GET /v1/products/{id}` refreshes the chosen merchant offer before a quote is persisted. Never trust amount, currency, product title, availability or member count from the browser. Ignore unknown currencies, prices with excessive fractional precision, non-HTTPS URLs and non-in-stock offers. Only validated offers can be proposed.

An explicit, consented area/asset match is required for a draft; matched peers did not opt into buying and cannot be charged. Deterministic shares use integer minor units and allocate the remainder without inventing discounts or exchange rates. Proposed savings are upper-bound arithmetic under the stated assumption of separate identical purchases, not achieved savings. A 30-minute quote expiration and permanent historical snapshot prevent a stale price being represented as live. Stage 4 must independently re-confirm all finance/participation conditions before any payments.
