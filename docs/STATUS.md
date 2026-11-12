# Stage 7 — Deployment and submission handoff

Status: **Implementation and documentation committed; final CI/browser verification in progress. Real hosting, live provider QA, MP4/YouTube upload and Devpost submission are not yet completed.**

## Source changes

- Render Blueprint for a Python FastAPI API and demo PostgreSQL. Paid API tier for a safe pre-deploy Alembic migration; the free demo database is temporary. Deploying the blueprint requires separate account authorization and cost acceptance.
- Server readiness endpoint `GET /api/v1/ready` validates live DB access, Alembic revision `20261112_06`, and the funding ledger table. `GET /health` remains a lightweight process-only endpoint.
- Render-native `postgresql://` and `postgres://` driver strings normalized to `postgresql+psycopg://`; other drivers remain rejected. Sensitive URLs are not logged.
- Browser reservation CORS preflight corrected to include HTTP PUT; API and Next.js security headers added; authenticated workspace set to `noindex`.
- Independent, pinned Playwright Chromium suite: registration, real database need, opt-in, reload logout, and re-login. Runs from `apps/web/e2e` and may save screenshots as CI evidence.
- Read-only deployment verifier script, honest deployment instructions, actual Flute process/scene storyboard and a copy-ready Devpost submission draft, without invented URLs or claims.

## Not verified or not executed

- No Render or Vercel resource has been provisioned by these commits.
- No real Gemini/Channel3/PayPal sandbox credentials were used in CI; real e2e payment is pending.
- No Flute MP4, edited product video or public YouTube upload exists yet.
- No Devpost form has been submitted; the user must publish the video and submit before the official deadline.
- Rate limiting, independent commerce/escrow handling and physical fulfillment need further work before any actual public real-money service.

See [DEPLOYMENT.md](DEPLOYMENT.md), [DEMO_VIDEO.md](DEMO_VIDEO.md), [DEVPOST_SUBMISSION.md](DEVPOST_SUBMISSION.md) and [MANUAL_QA.md](MANUAL_QA.md).
