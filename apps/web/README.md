# ONE / MANY Web

Next.js 16 App Router, TypeScript, Tailwind CSS v4, Motion, tsParticles, AG Grid Community, and Bryntum Scheduler Community. This is the actual authenticated frontend; product/capture/reservation outcomes must come from backend APIs and providers, never fabricated UI data.

## Local development

```powershell
# Start PostgreSQL and migrate the API first (see root README).
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

Set `NEXT_PUBLIC_API_URL` to the actual FastAPI **origin only**, e.g. `http://localhost:8000`. Do not place Gemini, Channel3 or PayPal keys in public frontend variables. API responses and user sessions are not persisted in client localStorage.

## Browser smoke

```powershell
npm run build:web
npm install --prefix apps/web/e2e
cd apps/web/e2e
npx playwright install chromium
npx playwright test
```

The test starts compiled Next.js and FastAPI, requires a migrated PostgreSQL instance and uses only a test auth secret plus disposable browser accounts. It verifies registration, creating a real opted-in need, browser reload and re-authentication. It cannot prove real Gemini/Channel3/PayPal payment correctness; see [Manual QA](../../docs/MANUAL_QA.md).

The root README and [deployment guide](../../docs/DEPLOYMENT.md) document Render + Vercel setup. Flute is configured **only on a separate demo branch**, using actual React components, as in [demo storyboard](../../docs/DEMO_VIDEO.md).

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
```
