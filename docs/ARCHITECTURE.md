# Architecture

ONE / MANY converts separate customer needs into compatible shared purchases. **Stage 0 implements only the visual and service foundation.**

```text
Browser → Next.js App Router (apps/web)
              │ planned HTTP /api/v1 calls
              ▼
          FastAPI (apps/api) → PostgreSQL (local Docker Compose)
              │ planned server-side adapters
              ├── AI requirement extraction
              ├── Channel3 product discovery
              └── PayPal Sandbox contributions and verified webhooks

Future frontend integration: Bryntum scheduling; AG Grid funding/ownership records
```

The diagram includes future connections. Currently the web routes render without API calls; the API exposes liveness without a database query. No business tables or integration adapters exist.

## Responsibilities

- **Web:** responsive landing page, application navigation, design tokens, accessible reusable components, and honest empty states. Next.js App Router and TypeScript with Tailwind CSS v4, shadcn/ui, selective Aceternity components, Motion, tsParticles, and Lucide.
- **API:** HTTP contracts, environment validation, JSON logging, centralized errors, CORS policy, and database connection configuration. Future business validation and integration credentials belong here.
- **PostgreSQL:** future durable domain records and transactional state. Compose provides an isolated local volume; SQLAlchemy and Alembic are prepared, but schema creation and migrations await the domain stage.
- **Docs:** durable handoff across Codex, ChatGPT, and human developers; record current reality separately from planned behavior.

## Trust boundaries

1. Browser input is untrusted. Future API endpoints must validate input, authenticate users, and authorize access to each resource; CORS is not authentication.
2. Environment secrets are backend-only. `NEXT_PUBLIC_*` values are public and must never contain credentials.
3. AI output and external catalog data are untrusted suggestions. Backend rules must validate compatibility, prices, currency, allocation, and schedules before state changes.
4. A client redirect or frontend payment success screen never proves funding. PayPal server verification, signed/verified webhooks, idempotency, and amount/currency reconciliation are required before recording contributions.
5. Scheduling views and grid rows are presentation; backend authorization and consistency checks remain authoritative.
6. PostgreSQL binds to loopback locally. Use separate production credentials and infrastructure in a later deployment stage. Do not expose this development Compose service publicly.

## Contracts and integration policy

See [INTEGRATION_CONTRACTS](INTEGRATION_CONTRACTS.md). Only documented Stage 0 routes are implemented. Choose provider SDKs and verify licensing when their stages begin; Bryntum and any commercial grid features require a licensing decision before installation. No paid components are installed in Stage 0.
