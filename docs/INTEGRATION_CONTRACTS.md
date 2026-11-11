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
