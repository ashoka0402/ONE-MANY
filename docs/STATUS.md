# Status

Current stage: **Stage 1 — Identity, needs and persistence**.

## Implemented in Stage 1

- Registration and login with Argon2 password hashing and expiring JWT access tokens.
- A real authenticated Next.js workspace: create, list, edit, archive, and restore private needs.
- FastAPI owner-scoped API endpoints, error handling, token verification, date validation and list pagination.
- SQLAlchemy users/needs models and a versioned Alembic migration.
- Backend tests including cross-account access denial and invalid input/token paths.
- GitHub Actions validation of migrations on an actual PostgreSQL container, in addition to frontend checks and backend tests.

## Not yet built

AI intent extraction or matching, Channel3 products, purchase groups, PayPal sandbox payments, Bryntum calendars, AG Grid, real shared-asset fulfillment, hosted deployment and Flute video.

## Verification

Stage 0 was fully green in [GitHub Actions](https://github.com/ashoka0402/ONE-MANY/actions/runs/43083392264). Stage 1 checks must be verified against its newly committed workflow run before reporting complete. This editor cannot independently perform a local Postgres-backed browser test; CI provides controlled API/database verification.

## Known limitations

- Bearer tokens are held only in memory; reload requires re-login. No password reset, email verification, rate limiting, or multi-session management yet.
- Site visitors cannot see other users' needs (no matching/community visibility implemented).
- Needs are soft-archived, not permanently deleted.
- The workspace retrieves the latest 100 needs; full API pagination exists and should be added to UI if needed.
- No real payments, escrow, purchased assets, or supplier inventory exists. Any product visuals on the landing page are illustrative.
- Current PostgreSQL Compose is for local development and CI only; a deployed app needs a hosted persistent database and HTTPS.
