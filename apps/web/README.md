# ONE / MANY Web

Next.js App Router, TypeScript, Tailwind CSS v4 and the brand design system. Stage 1 adds the authenticated, persistent needs workspace at `/app`.

```powershell
# Root of repository, while PostgreSQL and FastAPI are running:
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

The `NEXT_PUBLIC_API_URL` browser variable should point to the FastAPI origin (default http://localhost:8000). The route `/app` supports registration, login, need creation, editing, archiving and reopening with **actual database requests**; it does not mock payment or AI responses.

Tokens stay in memory and expire in one hour. Refreshing the browser requires logging in again. Stage 2 will provide demand matching; Channel3, PayPal, Bryntum, and AG Grid are not yet wired.

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
```

The component in `src/components/ui/bento-grid.tsx` is adapted from Aceternity UI's publicly available example. Flute is deferred until there is a functioning demo.
