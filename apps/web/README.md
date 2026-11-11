# ONE / MANY Web

Next.js App Router, TypeScript, Tailwind CSS v4, Aceternity-inspired Bento Grid, Motion and tsParticles.

Run from the repository root:

```powershell
npm ci --prefix apps/web
Copy-Item apps/web/.env.example apps/web/.env.local
npm run dev:web
```

The app is at http://localhost:3000 and its honest, non-transactional workspace preview is at /app. The frontend does not yet call FastAPI or PayPal.

Checks:

```powershell
npm run lint:web
npm run typecheck:web
npm run build:web
```

**Important:** Use the committed lockfile. If dependencies were edited, regenerate it with `npm install --prefix apps/web --package-lock-only` before `npm ci`. Never commit `.env.local`.

The Bento Grid implementation in `src/components/ui/bento-grid.tsx` adapts the public Aceternity UI example: https://ui.aceternity.com/components/bento-grid.
The brand stylesheet in `src/app/brand.css` is loaded by `layout.tsx` after Tailwind globals; tsParticles is client-only and disabled for reduced-motion users. Flute is intentionally deferred until the functioning demo stage.
