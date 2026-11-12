# Integration contracts

API base: `/api/v1`; documented in FastAPI's `/docs`.

## Public routes

- `GET /health` — only liveness; not DB readiness.
- `POST /auth/register` — JSON `{email,display_name,password}`; 201 yields `{access_token,token_type,expires_in,user}`; duplicate email 409.
- `POST /auth/login` — JSON `{email,password}`; 200 yields auth response; invalid login 401.

Password must have 12–128 characters at registration. Access token expires in 60 minutes by default. `AUTH_SECRET` is required for auth, and `DATABASE_URL` for persistence. In production both are mandatory.

## Authenticated routes

Send `Authorization: Bearer <access_token>`.

| Method | Path | Result |
| --- | --- | --- |
| GET | /auth/me | Authenticated user identity without password hash |
| POST | /needs | Create owned need (201) |
| GET | /needs | List only caller's needs; `limit` 1–100, `offset` 0–10000, optional `status=open|archived` |
| GET | /needs/{uuid} | Read one owned need; 404 for unknown or not owned |
| PATCH | /needs/{uuid} | Partial update of owned need or status |
| DELETE | /needs/{uuid} | Soft archive one owned need (204); not physical deletion |

Need create payload:

```json
{"request_text":"Need a pressure washer next weekend","location_label":"Pune","needed_from":"2026-11-14","needed_until":"2026-11-15"}
```

Dates and location are optional. Need text must be 12–2000 characters. The end date cannot precede the start date. Need responses additionally contain server-assigned ID, owner_id, status and timestamps. No caller may assign owner_id or mark a payment status.

List response: `{items:[...],total,limit,offset}`.

Error response: `{"error":{"code":"http_401","message":"Unauthorized"}}` for HTTP errors, `{"error":{"code":"validation_error","message":"Request validation failed"}}` for Pydantic 422 validation, and a generic 500 without secrets for unexpected errors.

## Deferred provider contracts

AI outputs must be parsed/validated and cannot charge or fund a group. Channel3 products must retain real source identifiers, currency and retrieval time. Future PayPal records must verify amount, currency, payee and provider capture/signature server-side, with idempotency and replay protection. Bryntum is presentation, while API validates reservation conflicts. AG Grid must display only authorized verified records. Sponsor licenses must be checked before installation.


## Stage 2 — AI extraction and anonymous discovery

`POST /api/v1/needs/{uuid}/analyze` (owner-authenticated) accepts no body. It uses the exact stored request text, calls configured Gemini structured-output API, validates a canonical asset type/purpose, required and excluded features and `shareable` boolean, then persists a single cache record. On cache hit, no new model request is made. If the provider is missing/unavailable, returns HTTP 503 and does not invent an extracted intent. Editing request text invalidates the cached record.

`POST /api/v1/needs` and `PATCH /api/v1/needs/{uuid}` accept `discoverable` boolean. Creation defaults to false and Stage 1 records migrate as private. Archiving sets discoverable=false.

`GET /api/v1/needs/{uuid}/matches` requires the caller to own an open, opted-in, located, successfully AI-analyzed reusable need. The response includes `need_id` (caller-owned), `asset_type`, `area` (caller-supplied), `potential_members`, `non_overlapping_schedules`, `scheduling_confirmation_required`, `candidates_limited`, `status` and `explanation`. The response intentionally never includes peer IDs, raw requests, dates, or account details.

Match admission: same AI-normalized asset label and normalized self-reported area; different owners; opt-in on both sides; non-archived; shareable extraction; no direct feature contradiction; no overlapping full-day windows. Missing date bounds count as requiring confirmation. This is a *candidate discovery* result only; cannot be treated as a product selection, reservation, purchase group, payment, or verified geographic proximity.


## Stage 3 — Channel3 and draft shared-purchase quotes

- `POST /api/v1/needs/{need_id}/products/search` (owner, opt-in, open, AI-analyzed reusable asset with area): calls real Channel3 `POST /v1/search` with a canonical asset + explicit required features, configurable country/currency. Returns normalized products, in-stock retailer offers with positive exact price and HTTPS link, feature-evidence warnings, and real retrieval timestamp. No provider credentials in response.
- `POST /api/v1/needs/{need_id}/proposals` body `{"product_id":"<real Channel3 id>","offer_url":"<exact listed retailer URL>"}`: rechecks Stage 2 matching, requires at least one prospective peer, re-fetches product detail with Channel3 `GET /v1/products/{id}`, checks exact current offer, rejects contradictions/unsupported feature evidence and constructs a persisted `draft`. Client-supplied prices are not used.
- `GET /api/v1/proposals`: list up to 50 owner-only draft quote snapshots.
- `GET /api/v1/proposals/{id}`: returns only caller's draft; others receive 404.

Proposal response includes owner-owned need ID, provider product ID, merchant link, actual price/currency, prospect count, exact integer-minor-unit shares, hypothetical savings, quote expiry and disclaimers. No actual buyer commitments, fees or shipping are included. Future payment flows MUST reconfirm the price, offer, peer membership/consent, scheduling and amount before creating any PayPal order. No escrow, purchase, or PayPal charge is initiated.


## Stage 4 — Funding and Sandbox Orders v2

All routes under `/api/v1` unless noted.

- `POST /proposals/{id}/funding-group` — organizer-only, rechecks a fresh Stage 3 quote and live Channel3 offer; creates a recruiting pool and accepts the organizer's need. Returns `{group,invite_code}`; the code is only presented on creation or explicit rotation.
- `POST /funding/join` with `{invite_code,need_id}` — authenticated new member explicitly accepts a slot using their own open, opt-in, AI-analyzed need. Requires same normalized area and asset, compatible features and known non-overlapping date windows. No payment is made on joining.
- `POST /funding/groups/{id}/rotate-invite` — organizer-only while recruiting; invalidates old invite.
- `GET /funding/groups` and `GET /funding/groups/{id}` — authenticated members only; anonymized per-slot amounts and payment states, no other member's identity.
- `POST /funding/groups/{id}/paypal-order` — accepted member only after group fills, rechecks dates, consent and current Channel3 price, and creates/reuses one fixed-amount PayPal Sandbox order. Returns trusted PayPal approval URL; no browser-chosen amount.
- `POST /funding/groups/{id}/paypal-capture` — member only. Uses stored PayPal order, queries PayPal, captures with fixed idempotency key if approved, independently re-fetches and validates amount/currency/capture status and ID. A PENDING capture never counts as completed.
- `POST /paypal/webhook` — publicly reachable endpoint that verifies signature with PayPal Sandbox, deduplicates event IDs, and reconciles `PAYMENT.CAPTURE.COMPLETED` by fetching the stored order again. A verified `DENIED` or `REFUNDED` event triggers review and excludes the reversed share.

States: recruiting, funding, funded, needs_review, cancelled. Each payment attempt: creating, awaiting_approval, capture_pending, completed, needs_review, reversed. All PayPal flows are Sandbox-only merchant payments, not escrow or production transfers. The group is funded only when verified captures from every participant exactly sum to the quote.


## Stage 5 — Provisional reservations

All endpoints are authenticated, group-member-only, under `/api/v1`.

- `GET /funding/groups/{group_id}/reservations` returns group ID, product title, current group state, bookable flag, **caller's last version**, caller's own permitted need window, and active reservation rows (UUID, anonymous member slot number, inclusive start/end civil dates, version, is_you). No other member IDs, emails or raw descriptions.
- `PUT /funding/groups/{group_id}/reservation` accepts `{start_date:"YYYY-MM-DD",end_date:"YYYY-MM-DD",expected_version:N}`. Requires fully funded group with every accepted member's verified completed Sandbox contribution, current compatible opt-in needs, caller's own window, and non-overlap with other active reservations. The first write uses `expected_version=0`; subsequent changes must pass the latest caller-only version. Repeating the exact same active dates is idempotent. A successful write returns the updated board.
- `DELETE /funding/groups/{group_id}/reservation` cancels only caller's reservation, increments the version and returns the updated board. Repeating a cancellation is harmless. Cancellation remains available in review state.

PostgreSQL enforces `UNIQUE(group_id,user_id)` and an active-only GiST exclusion on group and inclusive `daterange(start_date,end_date+1,'[)')`. The API additionally locks the group row for serialization and checks overlap; races are caught as HTTP 409. Missing funding, date conflicts, or stale versions are rejected, never silently displayed as success.

This is a *provisional shared-use plan*, not a retailer purchase, verified physical inventory, handover contract, or timezone-precise reservation. The Bryntum timeline is read-only; the server is the only source of booking state.
