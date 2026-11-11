# Roadmap

Current stage: **0 — Foundation and design system** (frontend lint, types, build, API tests, Ruff and Compose configuration passed in GitHub Actions). Stop here until the next explicit user prompt. Target hackathon deadline: **November 13, 2026, 01:30 IST**. Later stages are a proposed sequence, not authorization to implement them.

| Stage | Scope | Acceptance criteria |
| --- | --- | --- |
| 0 | Foundation and design system | Monorepo, landing and honest app shell, accessible responsive tokens/motion, FastAPI health/settings/errors/logging/CORS, database configuration, Compose, handoff docs, verified checks and Git checkpoint. |
| 1 | Identity, needs, and persistence | Agreed domain schema and migrations; authenticated resource ownership; users can create/read/update needs; input and authorization tests. |
| 2 | AI extraction and compatible demand | Server-only AI integration with structured validated output, explicit failure states, compatibility rules and explainable suggestions; fixtures and contract tests. |
| 3 | Channel3 products and group proposals | Real product retrieval, normalized identifiers/currency/availability, deterministic group cost allocation, no fabricated catalog data; adapter and business-rule tests. |
| 4 | PayPal Sandbox contributions | Member-specific authorization, verified capture/webhook flow, idempotent reconciliation, amount/currency checks, cancellation and failure paths; sandbox evidence. |
| 5 | Shared-asset scheduling | License decision for Bryntum, server-authorized reservations, conflict rules, timezone policy and cancellation; scheduling tests. |
| 6 | Funding and ownership records | AG Grid license/feature decision, authorized ledger views from verified backend records, reconciled ownership and transparent statuses; access and calculation tests. |
| 7 | Demo readiness and hardening | End-to-end sandbox flow, accessibility/responsiveness/performance checks, secret and dependency review, documented demo/reset steps; deploy only with authorization. |

Every stage must preserve API contracts, update the handoff documents, run relevant verification, and report skipped or failing checks honestly. No stage may imply real funds or live payment readiness from sandbox behavior.
