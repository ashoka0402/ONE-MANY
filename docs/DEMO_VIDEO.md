# ONE / MANY — factual cinematic demo plan (under 3 minutes)

**Status: storyboard + rendering instructions, not an exported video.** The official PayPal AI Hackathon requires real working footage in a **public YouTube** video lasting **less than 3 minutes**. Submit a working clip, not only design mockups or a static AI animation.

## Narrative (2:35 target)

| Video time | What to show | Truthfulness gate |
| --- | --- | --- |
| 00:00–00:10 | Flute camera travel over the **actual ONE / MANY homepage**: "Many people. One smarter purchase." | A cinematic intro, not a substitute for app footage |
| 00:10–00:24 | Two genuine users with distinct needs: "Install shelves with a drill" vs "Mount curtain rods next week." | Separate actual test accounts, not fabricated business matches |
| 00:24–00:47 | User A creates a need, explicitly opts into anonymous discovery and runs real Gemini extraction | Record the real API response and resolved model |
| 00:47–01:02 | User B creates their own need; matching reveals a compatible opportunity | Show actual backend match count, no private identity leaks |
| 01:02–01:22 | Channel3 returns a **real** product and real in-stock merchant offer; draft quote shows exact member shares | Do not claim the catalog offer is final shipped price |
| 01:22–01:55 | Both members explicitly join a funding group, then approve **their own** PayPal Sandbox orders | Show PayPal Sandbox approval and actual verified capture, not a fake payment overlay |
| 01:55–02:12 | AG Grid ledger: accepted shares, server-verified captures, 100% only if actual test captures complete | Label payments Sandbox, not real money or escrow |
| 02:12–02:29 | Bryntum Community Scheduler: members select separate dates, reserve/cancel and refresh | Show persisted PostgreSQL bookings, not manually drawn bars |
| 02:29–02:35 | One-line value proposition and GitHub/reproducibility URL | Make no retailer-purchase or real-ownership claim |

Keep screen recordings legible: zoom browser to 110%–125% before capture. Avoid exposing passwords, login tokens, API secrets, full raw PayPal IDs, personally identifiable messages or private email inboxes. Never capture a real user's financial data. A short optional disclosure at the bottom: "Illustrative requests; real test accounts and provider Sandbox." Use owned or permitted music; silence with original narration is fine.

## Why Flute and what it can actually do

Flute composes deterministic camera/3D scenes **from real React DOM components**. It is not a prompt-to-MP4 video engine that creates a working checkout from screenshots alone. Use it to render a cinematic opening and closing segment, then cut in *real browser recordings* for Gemini, Channel3, PayPal and scheduling.

**Work on a separate branch** so Flute's development route and tooling do not ship with the production app:

```powershell
git switch -c flute-demo
cd apps/web
npm install @webprodigies/flute
npx flute init
npx flute guide --json
npm run dev
# In another terminal at apps/web:
npx flute open --url http://127.0.0.1:3000
```

Flute setup creates a `/flute` development route for Next.js. Have your coding agent read generated `FLUTE.md` and the official guide before composing. The scene must use the real existing marketing components and design tokens (not a screenshot-only slide or a disconnected fake dashboard). Example direction:

> Create a 9-second cinematic ONE / MANY intro, using actual homepage React components from this repository. Use deep charcoal with restrained electric-lime accents and crisp typography. Begin with two distinct user-need tiles orbiting a shared, empty space, then reveal the live app's ONE / MANY identity and the line "Many people. One smarter purchase." Add depth, elegant camera motion and subtle particles only where already part of the UI. Do not create fake payments or invent product records. Make all visuals legible, allow reduced motion and finish with a clean transition for the recorded dashboard clip. Inspect `FLUTE.md` and `npx flute guide --json` before writing a scene. Verify source snapshots and export.

Flute typically saves a `src/flute/scenes/*.scene.json` recipe and matching TSX. After creating new scene pairs, `npx flute sync` (outside Vite), then `npx flute scenes`, `npx flute snapshot --scene <name> --url http://127.0.0.1:3000`. These commands require the app's development server running. Install Chromium and FFmpeg for export:

```powershell
npx playwright install chromium
# Install FFmpeg using a trusted package manager on your computer.
npx flute export --url "http://127.0.0.1:3000/flute?flute-scene=one-many-intro" --output one-many-intro.mp4 --fps 60
```

**Verify the actual scene URL with `npx flute scenes` or the studio first.** The command above is an illustration and may need the URL produced by Flute's Export control.

## Production recording and final edit

1. Before filming, run the full real provider checklist in [MANUAL_QA.md](MANUAL_QA.md), preserving genuine but disposable demo accounts. Use private test-only browser profiles.
2. Record the product in two browser profiles, A and B. Keep demo narration brief. Ensure that **Capture verified** really corresponds to PayPal's fetched Sandbox COMPLETED state.
3. Capture the Flute introduction separately, then use any MP4 editor to assemble it with real screen recordings. Keep final length **2:35–2:50**, never 3:00 or more.
4. Export at least 1080p / 30fps H.264 MP4, then inspect the entire output with sound and subtitles. Verify PayPal and AG Grid/Bryntum logos are only used as integration references under their terms; avoid unlicensed tracks or unrelated trademarks.
5. Upload the final video to YouTube with visibility **Public**, not Private or Unlisted, and verify it plays signed out.
6. Place the real YouTube URL and working GitHub/demo URL in Devpost. The video file is not generated by this repository until you actually export and edit it.

Flute reference: https://github.com/webprodigies-org/flute . Official hackathon rules: https://paypalaihackathon.devpost.com/rules .
