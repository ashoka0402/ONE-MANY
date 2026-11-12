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
- [ ] Load AG Grid Community contribution ledgers for each member. Verify exact accepted shares, completed-capture totals, no pending-credit inflation, anonymous CSV contents, sorting/filtering and event-history ordering. Test a signed refund and review-state display.
- [ ] Complete deployment, a reproducible demo, Flute video and Devpost submission.


## Stage 7 publication gates — not performed by a source-code commit

- [ ] Inspect expected Render hosting charges and deliberately apply `render.yaml` in an authorized account, or choose the fully reproducible local route instead.
- [ ] Deploy Vercel from `apps/web`; set the exact HTTPS `NEXT_PUBLIC_API_URL`, `PUBLIC_WEB_URL` and `CORS_ORIGINS` values before trying cross-origin calendar PUTs.
- [ ] Confirm `/api/v1/ready` reports ready and run `python scripts/check_deployment.py --web-url ... --api-url ...`.
- [ ] Run `npm install --prefix apps/web/e2e` then the Playwright browser suite against a Postgres-backed API, and visually inspect the screenshot artifact.
- [ ] On a separate `flute-demo` branch, run `npx flute init` and `npx flute guide --json` with actual React app components; export an original cinematic intro, not a fabricated payment animation.
- [ ] Capture **real** Gemini, Channel3 and PayPal Sandbox app flows; verify the AG Grid ledger and Bryntum database-backed calendar on screen with two test accounts.
- [ ] Edit a final video **less than three minutes** with genuine working-app footage, original narration and permitted music; upload it **Public** on YouTube and check the link signed out.
- [ ] Verify repo is public, license visible and all setup instructions/links functional. Include judge test access instructions if needed, without publishing passwords in Git.
- [ ] Fill the Devpost project description and all required fields, paste real GitHub, working app/run instructions and public YouTube URLs. **Submit, not merely save draft**, by the stated deadline, then confirm submission.
