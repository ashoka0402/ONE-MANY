# Roadmap

Current stage: **3 — Channel3 catalog and saved draft shared-purchase proposals** (source implementation undergoing CI). Stage 4 PayPal Sandbox is next. Hackathon deadline: **November 13, 2026 at 01:30 IST**.

| Stage | Scope | Acceptance criteria |
| --- | --- | --- |
| 0 | Foundation / design | Complete: Next.js build, FastAPI health/tests, PostgreSQL smoke, docs and CI |
| 1 | Identity, needs and persistence | Account registration/login, ownership checks, Alembic migration, persistent need CRUD, real web forms, API tests, Postgres migration smoke |
| 2 | AI matching | Real Gemini structured extraction, explicit consent, privacy-preserving anonymous matching with conservative date/feature/area checks, provider failure and cache tests |
| 3 | Channel3/product proposals | Real API adapter, live-offer recheck, strict price validation, immutable owner-only draft snapshots and deterministic hypothetical splits; provider test fixtures in CI |
| 4 | PayPal Sandbox funding | Member-specific sandbox checkout, verified capture, idempotent reconciliation, cancellation and failure tests |
| 5 | Bryntum scheduling | Licensed integration, authorized reservations, conflict tests and timezone rules |
| 6 | AG Grid ledger | Verified contribution data, ownership breakdown and auditable presentation |
| 7 | Demo / delivery | Hosted functioning app or reproducible setup, end-to-end checkout demo, public GitHub license, <=3 minute YouTube video, Devpost |

No future stage is authorized by this roadmap. Changes to financial records require deterministic rules and tests.
