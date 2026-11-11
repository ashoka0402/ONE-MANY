# ONE / MANY — System Architecture

Stage 1 is the working identity and needs foundation. Matching, purchase proposals, payments, asset scheduling and ledger features remain separate future stages.

```text
Browser — Next.js App Router (/app)
  │ signup/login → token held in memory only
  │ /api/v1/auth/* and /api/v1/needs/*
  ▼
FastAPI — request validation → authorization → owned need CRUD
  │ PyJWT HS256 (60 min), Argon2 password hashing
  │ SQLAlchemy Session (one per request)
  ▼
PostgreSQL 17 — users, needs tables
  ▲
  └─ Alembic migration 20261112_01
```

## Service responsibilities

- **Next.js:** polished account screens, need submission and management, API error states, static stage-preview navigation. Client tokens are in React state (lost on refresh; no localStorage).
- **FastAPI:** input contracts, identity, password verification, signed access tokens, owner authorization, pagination, date constraints, CORS and normalized error responses.
- **PostgreSQL:** users and owner-scoped needs, unique normalized email, status/date constraints and indexed queries. SQLAlchemy writes use transactions. Alembic owns schema migrations.
- **AI, Channel3, PayPal, Bryntum, AG Grid:** deliberately not yet implemented.

## Trust boundaries

1. Browser-provided identity, dates, and need text are untrusted. FastAPI validates all input and derives owner_id from verified token only.
2. Passwords are hashed with Argon2; token signing and DB credentials are backend-only, never NEXT_PUBLIC variables.
3. Need lookup and mutation always filter by owner_id; cross-account access receives the same 404 as unknown IDs.
4. CORS only permits declared origins and headers; it is not access control.
5. Browser-held access tokens can be exposed by XSS: this prototype intentionally keeps tokens only in memory and requires re-login on refresh, limiting persistence. Before production use, adopt secure httpOnly session cookies, CSRF protections, refresh-token rotation, rate limiting and account recovery.
6. AI suggestions and catalog data must never bypass deterministic pricing, compatibility, scheduling or transaction verification.
7. PayPal contribution records may only be recognized after verified server-side capture, not a browser redirect. Do not implement unauthorized escrow or claim purchases occurred.

## Data model

- `users`: UUID, normalized unique email, display name, Argon2 password hash, created timestamp.
- `needs`: UUID, owner UUID FK, free-text intent, optional location, optional date window, status (`open`/`archived`), created and updated timestamps.
- Future stages add normalized extracted requirements, product candidates, matching proposals, groups, contributions and bookings by migration rather than speculatively building empty tables today.

See [INTEGRATION_CONTRACTS](INTEGRATION_CONTRACTS.md) for the API and [STATUS](STATUS.md) for actual verification.
