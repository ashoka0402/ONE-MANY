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
