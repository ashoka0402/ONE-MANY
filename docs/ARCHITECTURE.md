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
