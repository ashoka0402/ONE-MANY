# ONE / MANY — Devpost submission draft

**Status: ready-to-adapt copy, NOT an actual submitted entry.** Replace bracketed links only after verifying that they exist. Public GitHub source: https://github.com/ashoka0402/ONE-MANY .

## Project name

**ONE / MANY — Many people. One smarter purchase.**

## Short tagline

An AI-assisted way to turn separate local needs into transparent, consent-based shared purchases and usage plans.

## The problem

People often buy durable tools or equipment for occasional use: a power drill for a shelf, a pressure washer for a weekend, a projector for one event. Neighbors may need the same asset at different times without realizing it. That fragmented demand leads to unnecessary individual purchases and idle equipment.

## Our solution

ONE / MANY lets each person describe what they need in natural language. Gemini extracts a structured reusable asset and required features. The backend matches only opted-in, compatible needs in the same self-reported area and checks that proposed usage dates are separate. Channel3 supplies real catalog candidates and merchant offers. An organizer can create a draft shared quote from a currently available offer, with exact cents allocated by deterministic server-side logic.

A funding group is **not** created by AI, and anonymous matches are never charged. Each person must explicitly join an invitation using their own compatible request, then authorize only their own contribution via PayPal Orders v2 **Sandbox**. A server-verified completed capture is recorded as a test contribution; unapproved, pending or reversed payments cannot be counted as funded. AG Grid provides anonymous financial transparency and an append-only event history. After every Sandbox contribution verifies, Bryntum Scheduler Community provides a date-only, non-overlapping shared-use plan backed by PostgreSQL.

This is a **functional hackathon prototype**, not a live marketplace, escrow product, legal co-ownership service or physical retailer checkout. Sandbox transactions use no real money. In-stock catalog offers do not imply shipping, tax or fulfillment.

## Why PayPal and AI are both central

- **AI (Gemini):** converts independently described needs into validated reusable-asset intent, enabling new demand discovery that ordinary keyword searches miss.
- **PayPal Orders v2 Sandbox:** demonstrates the participant-by-participant authorization and verified capture workflow that transforms a compatible group into an actually reconciled *test* funding state. The app cannot claim a completed contribution until the backend independently checks PayPal.
- **Deterministic safety layer:** exact prices, feature constraints, explicit consent, member access and scheduling conflicts are handled by server-side rules, not generative text.

## Technology

Next.js 16, TypeScript, Tailwind CSS, Aceternity-inspired design, Motion for React, tsParticles, FastAPI, Python, SQLAlchemy, Alembic, PostgreSQL, Gemini API, Channel3 API, PayPal Orders v2 Sandbox, AG Grid Community, Bryntum Scheduler Community. GitHub Actions validates the API, Next.js build, PostgreSQL migrations and Chromium UI smoke. **Render is used only if the deployment actually runs on Render; do not claim it as a live sponsor integration otherwise.** Flute is used for a real-UI cinematic video intro only if the scene is successfully rendered.

## Features

1. Privacy-first authenticated natural-language requests, with opt-in anonymous matching.
2. Gemini structured asset extraction and deterministic compatibility checks.
3. Channel3 merchant-backed product discovery and verified draft cost allocation.
4. Member-approved invitation groups and idempotent PayPal Sandbox captures.
5. Anonymized AG Grid contribution and audit ledger.
6. Bryntum shared-use calendar with PostgreSQL-enforced non-overlapping dates.

## Links to fill only after verification

- Public repository: https://github.com/ashoka0402/ONE-MANY
- Working application URL: **[add deployed HTTPS URL, or state that the public README contains complete local run instructions]**
- Demo video: **[add verified PUBLIC YouTube link under three minutes]**
- Test access details: **[describe how judges obtain safe demo accounts, if needed; do not commit passwords or tokens]**

## How to run

Follow the repository [README](../README.md) and [deployment guide](DEPLOYMENT.md). Configure PostgreSQL and apply Alembic migrations. Add Gemini and Channel3 credentials plus PayPal Sandbox business and buyer accounts. Use separate accounts to demonstrate matching, enrollment and approvals. A working build is required; screenshots without functional access are insufficient.

## Honest current limitations and future improvements

- No actual purchase, shipping, shared legal title, vendor settlement, tax calculation or physical handover.
- No live PayPal mode; all payments are Sandbox only.
- Location is self-reported; date-only reservations need real handover/buffer modeling.
- AI catalog feature compatibility is conservative and requires human inspection before any purchase.
- Further identity/rate-limit controls and independent operational audit are needed before a real-money public launch.

## Final submission checklist (official rules)

- [ ] Public repository with visible MIT or other acceptable open-source license.
- [ ] Complete working code and setup instructions, or verified hosted app.
- [ ] Meaningful PayPal developer platform + AI usage shown working.
- [ ] Public YouTube demonstration **less than 3 minutes**, showing actual app in use.
- [ ] Fill in all Devpost project fields and provide all links.
- [ ] Check tools/brands only if actually integrated and permitted.
- [ ] Submit entry before **November 12, 2026, 12:00 PM PST = November 13, 2026, 01:30 AM IST**.
- [ ] Verify Devpost shows a successful submission (saving a draft is not submission).

Official rules: https://paypalaihackathon.devpost.com/rules
