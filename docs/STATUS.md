# Stage 5 — Bryntum scheduling and shared-use reservations

Status: **Stage 5 complete at the automated build/test level**. Browser-level and live third-party QA remain deferred.

## Implemented

- Bryntum Scheduler Community v8 (MIT, public npm) inside a client-only Next.js timeline, without a commercial license key.
- Client displays *real authenticated reservation rows* as read-only scheduler events; no fictional demo events or hardcoded booking data.
- Date-only REST APIs: GET reservations, PUT the caller's own reservation with an optimistic version, DELETE/cancel the caller's reservation.
- Booking permitted only for an explicitly accepted group with all independently verified Sandbox captures and matching total. Need eligibility and non-overlapping member windows are revalidated.
- Reservations restricted to the caller's own need window; only one active booking per group/member; only members may view anonymous slot labels.
- Cancelled rows remain in the database with incremented versions, but disappear from the shared active timeline. An owning member can rebook using the returned `own_version`.
- Group-row locking and an independent PostgreSQL GiST exclusion constraint prevent concurrent overlapping active date windows.
- A `needs_review` group blocks edits/new reservations but permits cleanup cancellation.
- Tests cover authorization, unfunded state, stale versions, invalid date windows, cancellation/rebooking, privacy, app-level conflicts and DB-level overlap exclusion.

## Test status

[GitHub Actions run 43164775217](https://github.com/ashoka0402/ONE-MANY/actions/runs/43164775217) passed **45 Python tests**, Ruff lint, frontend ESLint and TypeScript, Next.js production build with Bryntum Community v8, Alembic migration `20261112_05` against PostgreSQL, authenticated reservation write/read smoke, a deliberate GiST overlap violation, and Compose validation. Temporary dependency lockfile generation was removed from the permanent workflow; CI is read-only.

## Deferred manual checks

Live Gemini and Channel3 keys, PayPal Sandbox buyer authorizations/capture, incoming verified webhooks, cross-browser Bryntum visual checks and deployment are intentionally reserved for the final validation. No physical asset has been delivered; all bookings are provisional.
