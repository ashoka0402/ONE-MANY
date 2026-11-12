# Roadmap

Current stage: **4 — member-approved PayPal Sandbox funding and capture verification** (automated checks passed; Stage 5 awaits authorization). Hackathon deadline: **November 13, 2026 at 01:30 IST**.

| Stage | Scope | Acceptance criteria |
| --- | --- | --- |
| 0 | Foundation / design | Complete: Next.js build, FastAPI health/tests, PostgreSQL smoke, docs and CI |
| 1 | Identity, needs and persistence | Account registration/login, ownership checks, Alembic migration, persistent need CRUD, real web forms, API tests, Postgres migration smoke |
| 2 | AI matching | Real Gemini structured extraction, explicit consent, privacy-preserving anonymous matching with conservative date/feature/area checks, provider failure and cache tests |
| 3 | Channel3/product proposals | Real API adapter, live-offer recheck, strict price validation, immutable owner-only draft snapshots and deterministic hypothetical splits; provider test fixtures in CI |
| 4 | PayPal Sandbox funding | Implemented: explicit participant join, sandbox Orders v2 checkout, independent capture verification, idempotent retries, signed webhook handling, 41 passing backend tests and PostgreSQL smoke |
| 5 | Bryntum scheduling | Licensed integration, authorized reservations, conflict tests and timezone rules |
| 6 | AG Grid ledger | Verified contribution data, ownership breakdown and auditable presentation |
| 7 | Demo / delivery | Hosted functioning app or reproducible setup, end-to-end checkout demo, public GitHub license, <=3 minute YouTube video, Devpost |

No future stage is authorized by this roadmap. Changes to financial records require deterministic rules and tests.
