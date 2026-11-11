# Integration contracts

## Implemented in Stage 0

Development API origin: `http://localhost:8000`. API version prefix: `/api/v1`.

`GET /api/v1/health` returns HTTP 200:

```json
{"status":"ok","service":"one-many-api","version":"0.1.0"}
```

This endpoint reports process liveness only. It does not access PostgreSQL, AI, products, payments, or scheduling services. No authentication is required for this public liveness response.

Application error responses use:

```json
{"error":{"code":"http_404","message":"Not Found"}}
```

HTTP errors use `http_<status>` and a safe status phrase. Invalid request data uses HTTP 422 with `validation_error` / `Request validation failed`. Unexpected failures use HTTP 500 with `internal_error` / `Internal server error`. Responses omit submitted values, exception details, and secrets. Native CORS preflight responses are middleware protocol responses, not domain errors.

The configured browser origin defaults to `http://localhost:3000`. Stage 0 allows GET, Content-Type, and no cross-origin credentials. Future authenticated or mutating endpoints must explicitly update policy and tests. API documentation is available at `/docs` and `/openapi.json`.

## Planned boundaries — no endpoints or adapters implemented

| Integration | Owner and responsibility | Required verification before implementation is complete |
| --- | --- | --- |
| AI | API validates extracted needs and compatibility suggestions | Structured schema, malicious input and invalid output handling, timeouts, provider failures, server-side credentials; suggestions are not business authority. |
| Channel3 | API retrieves real products and normalizes catalog records | Verify current provider API; preserve source IDs, prices/currencies, availability and retrieval time. Never silently replace failures with fake products. |
| Group business logic | API calculates member allocations and candidate schedules | Deterministic calculations, integer minor currency units, explicit rounding, membership/ownership authorization and atomic state changes. |
| PayPal Sandbox | API creates/verifies individual contribution flow and reconciles webhooks | Verify IDs, amount/currency, payee, signature/provider verification, idempotency and replay handling. Browser callbacks cannot mark a group funded. |
| Bryntum | Web displays usage calendar; API owns reservations | License availability, timezone policy, authorized access and backend conflict checks. Do not install commercial components before the license decision. |
| AG Grid | Web displays API-authorized funding and ownership rows | Community vs enterprise feature/license decision, verified underlying data, safe rendering and resource access control. |

Future route names, provider payloads, schema details and financial state machines must be agreed in their requested stage. This document intentionally does not promise undocumented third-party APIs.
