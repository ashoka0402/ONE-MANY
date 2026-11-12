# ONE / MANY engineering instructions

Read [STATUS](docs/STATUS.md), [ROADMAP](docs/ROADMAP.md), and [ARCHITECTURE](docs/ARCHITECTURE.md) before making changes. Consult [DECISIONS](docs/DECISIONS.md) and [integration contracts](docs/INTEGRATION_CONTRACTS.md) for relevant decisions.

- Stage 3 is the current scope. Do not implement Stage 4 or later without explicit request. Catalog data must be from real providers, price math must be deterministic, drafts are NOT funded/accepted purchases. Preserve the authenticated user-owned needs API.
- Preserve the Next.js frontend / FastAPI backend architecture and stable `/api/v1` contracts.
- Make minimal, scoped changes. Reuse existing components and dependencies; do not rewrite unrelated modules.
- Keep TypeScript in `apps/web`, Python in `apps/api`, and architecture / handoff documents in `docs`.
- Handle small tasks directly. Delegate only bounded independent work; assign explicit file ownership and avoid overlapping writes. Wait for dependencies before integration.
- Keep all secrets server-side and out of Git, browser bundles, responses, and logs. `.env.example` contains placeholders only.
- Never fabricate successful tests, integration results, payment status, or AI responses. Mark nonfunctional UI as coming later.
- Run the relevant tests, lint, type checks, and build before reporting completion. State exactly what failed or could not run.
- Review correctness, trust boundaries, accessibility, and security. Respect reduced motion and keep decorative layers noninteractive.
- Do not deploy, publish, delete production data, or bypass checks without explicit authorization.
- Update STATUS and relevant architecture, decisions, contracts, and roadmap documents after every stage, including actual verification results and limitations.
- Use npm for the frontend and Python >=3.12 for the backend. Node must be >=22.12. Do not introduce paid components or speculative frameworks.

The six available specialist responsibilities are research, implementation, testing, review, docs-ui, and security. Availability does not require spawning every agent; keep concurrency within the current host limit.
