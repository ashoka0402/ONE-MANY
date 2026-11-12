# ONE / MANY — Stage 7 deployment handoff

**No hosted service has been created by committing these files.** This guide gives a reproducible process; external account ownership, real URLs, secrets, and a browser verification are still required.

## Recommended split

- **Vercel:** Next.js web app from repository `apps/web`.
- **Render:** FastAPI from `apps/api` plus PostgreSQL, using root `render.yaml`.
- **PayPal:** Sandbox only; no Live API endpoint, escrow, automatic refunds or real orders.

The Render Blueprint uses a paid `0.5c-512mb` API instance to support `preDeployCommand: python -m alembic upgrade head`. **Review charges before applying.** The declared free PostgreSQL database is a short-lived demo resource and is **not suitable for durable production data**. You may choose a paid database instead. A paid or production account is not required merely to run this project locally for judges.

## 1. Render API and database

1. In the Render dashboard, **Blueprints → New Blueprint Instance**, connect [ashoka0402/ONE-MANY](https://github.com/ashoka0402/ONE-MANY), and select root `render.yaml`. Inspect planned charges before proceeding.
2. Set `PUBLIC_WEB_URL` to the **exact final Vercel origin** (HTTPS, no path or trailing slash). If Vercel is not deployed yet, configure a temporary HTTPS origin and update it immediately after Vercel is ready.
3. Set `CORS_ORIGINS` to a **JSON array of your real Vercel origin**, e.g. `["https://your-site.vercel.app"]`. No trailing slash, wildcard, or localhost in a public deployment.
4. Enter the real backend-only `GEMINI_API_KEY`, `CHANNEL3_API_KEY`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`; add `PAYPAL_WEBHOOK_ID` after registering a Sandbox listener. **Never commit these secrets to GitHub**. You can leave optional providers unset for an initial liveness-only deployment, but their workflows will return errors until configured.
5. `AUTH_SECRET` is auto-generated. `DATABASE_URL` comes directly from Render Postgres; the application normalizes native `postgresql://` to the explicitly supported psycopg 3 dialect.
6. Wait for the **pre-deploy migration** to finish and the service to become healthy at `https://<your-api>.onrender.com/api/v1/ready`. The `/health` endpoint alone is only a process liveness probe. `/ready` checks database connectivity and Alembic revision `20261112_06`.

**Cost warning:** Render's safe pre-deploy command is not supported on free web services. This Blueprint deliberately avoids running migrations on every web worker startup. Do not click Apply until you accept the provider's displayed pricing.

## 2. Vercel Next.js frontend

1. Vercel → Add New → Project → import `ashoka0402/ONE-MANY`.
2. Set **Root Directory** to `apps/web`; Framework: Next.js. Keep normal Next.js build and start settings.
3. Set `NEXT_PUBLIC_API_URL` to the actual Render API HTTPS origin, **not** the `/api/v1` path, e.g. `https://your-api.onrender.com`. This variable is public by design; API keys do not belong here.
4. Deploy. Open `https://<your-site>.vercel.app` and `https://<your-site>.vercel.app/app`.
5. Update Render `PUBLIC_WEB_URL` and `CORS_ORIGINS` to that exact Vercel origin and redeploy the API; if the Render URL changed, update Vercel's `NEXT_PUBLIC_API_URL` and **redeploy** (Next.js embeds public env values at build time).
6. Run `python scripts/check_deployment.py --web-url https://your-site.vercel.app --api-url https://your-api.onrender.com`. This uses no provider credentials and performs no payments.

## 3. PayPal Sandbox wiring

1. Create a PayPal Sandbox **merchant/business** test account and a separate Sandbox **buyer/personal** test account; do not reuse the merchant as a buyer.
2. Create an app in PayPal Developer Dashboard; set `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` in Render only.
3. Register a **Sandbox** webhook target at `https://<your-api>.onrender.com/api/v1/paypal/webhook`. Subscribe to `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.PENDING`, `PAYMENT.CAPTURE.DENIED`, and `PAYMENT.CAPTURE.REFUNDED`. Set the returned `PAYPAL_WEBHOOK_ID` in Render.
4. Verify two distinct opted-in members, real Gemini output, an authentic Channel3 offer, each member's own PayPal approval, and the final completed capture ledger. After each PayPal redirect, **sign in again** (tokens stay in memory), load funding groups and explicitly verify/capture the approved order.
5. Test a non-approval, expired group, changed merchant price, amount mismatch, replayed webhook, and refund/reversal review state. Do not publish real credentials, personal buyer data, or raw PayPal debug payloads.

**Demo pricing:** The code's default Channel3 locale is US/USD and the PayPal adapter is permanently Sandbox-only. INR is not silently converted. Actual merchant stock and shipping/handover are outside this prototype.

## 4. Functional demo and Devpost

Official rules allow **either** a hosted working demo **or** complete setup/run instructions in the public repository. Hosting is not mandatory, but an inert mockup does not qualify. If accounts are required to judge a hosted build, provide temporary demo credentials through the appropriate submission instructions, never commit credentials to the public repository.

Run the Chromium smoke test after locally applying Alembic migrations:

```powershell
npm ci --prefix apps/web
npm install --prefix apps/web/e2e
cd apps/web/e2e
npx playwright install chromium
npx playwright test
```

A running PostgreSQL server is required. Playwright launches the built Next.js server and FastAPI server; run `npm run build:web` first. The browser test registers a test user, saves a real need, reloads, and signs back in. It does **not** fake Gemini, Channel3, or PayPal success.

Follow [FINAL QA](MANUAL_QA.md) and [DEMO VIDEO](DEMO_VIDEO.md) before submitting. See the official [Devpost rules](https://paypalaihackathon.devpost.com/rules) and [submission draft](DEVPOST_SUBMISSION.md).
