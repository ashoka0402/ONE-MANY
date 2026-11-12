# Final manual QA — intentionally deferred until all development stages finish

This is a checklist, **not evidence** that these steps have been performed.

- [ ] Configure local PostgreSQL, `DATABASE_URL`, unique `AUTH_SECRET`; apply `alembic upgrade head`.
- [ ] Configure a valid Gemini key and analyze multiple genuine natural-language requests. Verify extracted asset labels/feature requirements and provider failure behavior.
- [ ] Configure a genuine Channel3 key. Search products, inspect actual in-stock merchant offers and verify the price recheck before saving a draft.
- [ ] Create two or more separate accounts, opt each compatible need into discovery and supply non-overlapping, complete usage dates.
- [ ] Create a time-limited funding group; copy its invitation securely. Join from independent accounts, checking that another user cannot see or change private needs.
- [ ] Configure a PayPal Sandbox app/merchant and independent buyer test accounts. Approve each share, sign back in, verify capture and check exact ledger sums.
- [ ] If deployed, configure HTTPS `PUBLIC_WEB_URL`, a webhook listener and Sandbox `PAYPAL_WEBHOOK_ID`; confirm signature verification, event replay and a reversal path.
- [ ] Open the Bryntum Community timeline for each member, save a subset of their own need dates, verify both accounts see the persisted booking, then edit and cancel it. Confirm date-range rejection, member isolation, and all-day rendering.
- [ ] Verify responsiveness, contrast, keyboard navigation, reduced-motion handling, reload persistence (with login re-entry), and full screenshots in real browsers.
- [ ] Build the Stage 6 AG Grid verified contributions interface if authorized, then complete deployment, a reproducible demo, Flute video and Devpost submission.
