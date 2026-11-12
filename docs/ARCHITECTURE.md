# ONE / MANY — Stage 2 Architecture

```text
Next.js authenticated workspace
  | POST /needs/{id}/analyze (explicit user action)
  v
FastAPI owner auth → Gemini adapter (server-side key, JSON schema, strict validation)
  |                          |
  |                          +-- provider error / invalid output → 503, NO fake data
  v
need_intents (PostgreSQL via Alembic migration)
  | asset_type, asset_key, purpose, feature constraints,
  | shareable, model, source_hash, timestamp
  v
GET /needs/{id}/matches (owner + discoverable + shareable + located)
  |
  +-- candidate search: open + opted in + same area + different owner
  +-- conservative deterministic gates: same normalized asset type;
  |                                 feature exclusions; separate known dates
  +-- group by different owner, no raw peer data returned
  v
Anonymous potential-member count + schedule confirmation requirements
```

## Critical trust boundaries

1. Only logged-in owners may analyze or query a need. Token verification and SQL owner checks are always performed.
2. Need descriptions are not automatically sent to external AI providers. Clicking **Analyze** is the explicit user action that sends the text to Gemini.
3. All AI response content is treated as untrusted input, parsed as strict typed JSON, and checked before it can be persisted.
4. The model extracts a canonical asset label, not a product link, a verified specification, a shop, or a price. No AI output can initiate or approve payment.
5. Users opt in explicitly for each need; existing records remain private. Archiving removes discovery consent. Other users' raw descriptions, identities, dates and UUIDs never appear in matching responses.
6. The backend matches exact normalized asset and self-reported location labels and rejects explicitly contradictory features or overlapping complete date windows. Missing dates give *unconfirmed* scheduling.
7. Compatible labels do not establish physical proximity, market availability, shared ownership agreement, safety, or compatibility. Those require later provider and human confirmation.

## Data evolution

- Stage 1 `users` and `needs` remain.
- Stage 2 adds nullable normalized `needs.location_key`, server-default-false `needs.discoverable`, and `need_intents` (one per need, FK cascade, extracted fields, cache fingerprint and provider identity).
- Alembic migration backfills area keys without changing privacy choices.
- Stage 3 will introduce product/real-catalog data; Stage 4 adds financial state machines; do not create those schemas now.

See [INTEGRATION_CONTRACTS](INTEGRATION_CONTRACTS.md) and [STATUS](STATUS.md).


## Stage 3 catalog and pricing architecture

```text
Owned, opted-in, AI-analyzed reusable need
   | POST /needs/{id}/products/search — explicit search action
   v
Channel3 REST API (server key) → validated product/merchant offers
   | one of the returned product IDs + URLs selected by owner
   v
POST /needs/{id}/proposals
   |
   +-- re-check owner and source-hash freshness
   +-- re-run Stage 2 anonymized potential-member count
   +-- fetch Channel3 product detail fresh by exact ID
   +-- compare exact selected HTTPS offer URL against provider records
   +-- require in-stock, supported currency, valid price and no exclusions
   +-- compute integer-minor-unit equal shares (sum == price)
   v
purchase_proposals — immutable unapproved quote snapshots
   |
   v
GET /proposals — owner only
```

Business constraints: product search does not auto-purchase. Only a server-validated real retailer offer can produce a draft; browser amount fields are not trusted. Matching members are prospective, not committed. The price snapshot expires after 30 minutes and Stage 4 must revalidate offer amount/currency, participants and terms before any PayPal action. No credit card or PayPal token is handled in Stage 3.


## Stage 4 — Explicitly accepted PayPal Sandbox funding

```text
Stage 3 Channel3 quote (fresh, selected merchant offer)
  -> POST /proposals/{id}/funding-group
  -> Organizer automatically accepts a slot; invitation code stored as SHA-256 hash
  -> Each invited account submits an independently compatible need and joins explicitly
  -> All slots accepted, dates and features rechecked => funding
  -> Each member creates ONE persisted PayPal Sandbox order at fixed share amount
  -> Buyer approves on www.sandbox.paypal.com
  -> Re-authenticate, then server GETs order and captures with stable idempotency key
  -> Server GETs the order again, validates single COMPLETED capture
  -> All verified captures, exact summed amount => funded
  -> Any signed reversal/denial or captured-amount mismatch => needs_review
```

**Database:** `funding_groups` stores an owner, immutable quote reference, hashed invitation, target size, fixed total and expiry. `funding_members` stores unique user/need/slot and accepted share. `payment_attempts` stores one order per member/group with unique PayPal order and capture IDs and a durable request key derived from its UUID. `paypal_webhook_events` retains verified event IDs against retries and replay. Alembic revision `20261112_04` owns all tables.

**Trust boundaries:** The frontend never supplies a price, capture ID or PayPal order for reconciliation. PayPal OAuth credentials and Channel3 keys stay on the backend. An API-approved return URL is not proof of payment. Orders are checked against expected group/reference, per-member custom_id, currency, exact amount and a single completed capture. PayPal webhooks must pass PayPal signature verification and are reconciled to the stored order before marking completed. Reversed captures are excluded from the ledger. No production PayPal endpoint, escrow, automatic refunds or physical retailer order is included.
