"use client";

import dynamic from "next/dynamic";
import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowLeftRight, ArrowRight, ArrowUpRight, CalendarDays, Check,
  CheckCircle2, ChevronRight, CircleHelp, FileText,
  Handshake, Lightbulb, LogOut, Play, ReceiptText, ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { AuditRow, MemberRow } from "@/components/ag-ledger-grid";

const DemoLedgerGrid = dynamic(
  () => import("@/components/ag-ledger-grid").then(m => m.AgLedgerGrid),
  { ssr: false, loading: () => <p className="pd-loading">Preparing the sample contribution ledger…</p> },
);
const DemoTimeline = dynamic(() => import("@/components/bryntum-schedule"), {
  ssr: false, loading: () => <p className="pd-loading">Preparing the sample Bryntum timeline…</p> },
);

type Stage = "needs" | "quotes" | "funding" | "ledger" | "schedule";
type GroupId = "washer" | "projector";
type Phase = "awaiting_approval" | "approved" | "completed";
type Scenario = {
  id: GroupId; product: string; description: string; area: string;
  price: number; people: number; window: string; ref: string;
};
const scenarios: Scenario[] = [
  { id: "washer", product: "Pressure washer", description: "Clean the patio and shared outdoor space", area: "Baner, Pune", price: 400, people: 4, window: "Nov 16–22", ref: "DEMO-Q-001" },
  { id: "projector", product: "Portable projector", description: "A neighborhood movie night", area: "Aundh, Pune", price: 360, people: 3, window: "Nov 25–30", ref: "DEMO-Q-002" },
];
const needs = [
  { title: "Clean my patio before the weekend", asset: "Pressure washer", description: "I need something to wash the patio and garden tiles.", area: "Baner, Pune", dates: "Nov 16–17", matches: 3, group: "washer" as GroupId, feature: "Outdoor cleaning" },
  { title: "Project a movie in the courtyard", asset: "Portable projector", description: "A projector for our neighborhood film night.", area: "Aundh, Pune", dates: "Nov 27–28", matches: 2, group: "projector" as GroupId, feature: "Outdoor viewing" },
  { title: "Put up shelves in my apartment", asset: "Cordless drill", description: "I need a drill for a few shelves in the study.", area: "Hinjawadi, Pune", dates: "Dec 02–03", matches: 1, group: null, feature: "Household repair" },
];
const steps: { id: Stage; name: string; kicker: string; description: string; icon: typeof Lightbulb }[] = [
  { id: "needs", name: "Your needs", kicker: "01 / NEED DISCOVERY", description: "Describe the problem and find compatible people.", icon: Lightbulb },
  { id: "quotes", name: "Draft quotes", kicker: "02 / COST SHARING", description: "Review an example item price and the individual shares.", icon: FileText },
  { id: "funding", name: "Group funding", kicker: "03 / PAYPAL SANDBOX", description: "See explicit acceptance and individual approval states.", icon: Handshake },
  { id: "ledger", name: "Contribution ledger", kicker: "04 / AG GRID", description: "Inspect participant and event records in a real data grid.", icon: ReceiptText },
  { id: "schedule", name: "Scheduling", kicker: "05 / BRYNTUM", description: "See when members plan to use the shared item.", icon: CalendarDays },
];
const money = (value: number) => "$" + value.toFixed(2);

function groupRows(id: GroupId, phase: Phase): { members: MemberRow[]; events: AuditRow[] } {
  const washer = id === "washer";
  const amounts = washer ? [100, 100, 100, 100] : [120, 120, 120];
  const states = washer
    ? ["completed", "completed", "completed", "completed"]
    : ["completed", "reversed", phase];
  const captured = washer
    ? [100, 100, 100, 100]
    : [120, 0, phase === "completed" ? 120 : 0];
  const updated = ["2026-11-12T08:40:00Z", "2026-11-12T08:47:00Z", "2026-11-12T09:04:00Z", "2026-11-12T09:11:00Z"];
  const members: MemberRow[] = amounts.map((amount, i) => ({
    slot: i + 1, is_you: washer ? i === 0 : i === 2,
    share_minor: amount * 100, share_display: money(amount),
    captured_minor: captured[i] * 100, captured_display: money(captured[i]),
    payment_state: states[i], last_updated_at: updated[i],
  }));
  const events: AuditRow[] = amounts.map((amount, i) => ({
    id: "fictional-" + id + "-" + i, recorded_at: updated[i],
    event_type: states[i] === "completed" ? "capture_completed" : states[i] === "reversed" ? "capture_reversed" : states[i],
    source: "demo_fictional", member_slot: i + 1,
    amount_minor: captured[i] * 100, amount_display: money(captured[i]),
  }));
  if (!washer && phase === "completed") events.push({
    id: "fictional-projector-new", recorded_at: "2026-11-12T09:14:00Z",
    event_type: "simulated_capture", source: "demo_fictional", member_slot: 3,
    amount_minor: 12000, amount_display: "$120.00",
  });
  return { members, events };
}

function HandoffDrawing() {
  const reduced = useReducedMotion();
  const [run, setRun] = useState(0);
  const [delivered, setDelivered] = useState(false);
  return (
    <div className="pd-handoff" aria-label="Cartoon illustration of one person handing a shared tool to another">
      <div className="pd-handoff-head">
        <div><strong>From my turn to yours.</strong><span>A little handover, a lot of shared value.</span></div>
        <button type="button" onClick={() => { setDelivered(false); setRun(n => n + 1); }}><Play size={14} /> Replay handoff</button>
      </div>
      <svg className="pd-handoff-svg" viewBox="0 0 520 198" role="img"
        aria-label="Two smiling neighbors passing a small pressure washer from left to right">
        <defs>
          <linearGradient id="pd-handoff-ground" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#345f42" stopOpacity=".35" /><stop offset="1" stopColor="#345f42" stopOpacity="0" /></linearGradient>
        </defs>
        <path d="M28 169 H493" stroke="#5f996e" strokeOpacity=".36" strokeWidth="2" strokeDasharray="6 8" />
        <ellipse cx="260" cy="171" rx="225" ry="22" fill="url(#pd-handoff-ground)" />
        <g className="pd-character person-left">
          <path d="M110 128 L98 163 M127 128 L137 163" stroke="#9fc0ad" strokeWidth="10" strokeLinecap="round" />
          <rect x="91" y="76" width="51" height="64" rx="22" fill="#73d6a4" />
          <circle cx="116" cy="54" r="25" fill="#d8bea8" />
          <path d="M92 50 Q90 22 116 28 Q145 28 140 50" fill="#2c382e" />
          <circle cx="107" cy="54" r="2.4" fill="#28382e" /><circle cx="123" cy="54" r="2.4" fill="#28382e" />
          <path d="M108 63 Q116 71 125 63" fill="none" stroke="#8e5147" strokeWidth="2.4" strokeLinecap="round" />
          <path d="M137 93 L172 111 L195 105" fill="none" stroke="#d8bea8" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M98 91 L81 117" fill="none" stroke="#d8bea8" strokeWidth="10" strokeLinecap="round" />
        </g>
        <g className="pd-character person-right">
          <path d="M386 128 L376 163 M407 128 L414 163" stroke="#a9b1c8" strokeWidth="10" strokeLinecap="round" />
          <rect x="374" y="76" width="49" height="64" rx="22" fill="#a8b7ee" />
          <circle cx="398" cy="54" r="25" fill="#dfc4ab" />
          <path d="M374 49 Q376 25 399 27 Q425 26 424 50" fill="#453c34" />
          <circle cx="389" cy="54" r="2.4" fill="#28382e" /><circle cx="407" cy="54" r="2.4" fill="#28382e" />
          <path d="M389 63 Q397 72 406 63" fill="none" stroke="#8e5147" strokeWidth="2.4" strokeLinecap="round" />
          <path d="M378 93 L340 114 L320 105" fill="none" stroke="#dfc4ab" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M418 94 L439 118" fill="none" stroke="#dfc4ab" strokeWidth="10" strokeLinecap="round" />
        </g>
        <motion.g key={run} initial={{ x: 0, y: 0, rotate: 0 }}
          animate={reduced ? { x: 142 } : { x: [0, 72, 142], y: [0, -24, 0], rotate: [0, -8, 0] }}
          transition={{ duration: reduced ? 0 : 1.55, ease: "easeInOut", delay: reduced ? 0 : .18 }}
          onAnimationComplete={() => setDelivered(true)}>
          <rect x="185" y="92" width="35" height="25" rx="7" fill="#b8f3c5" stroke="#436f50" strokeWidth="2" />
          <path d="M191 92 V86 Q191 82 195 82 H209 Q214 82 214 86 V92" fill="none" stroke="#b8f3c5" strokeWidth="5" />
          <circle cx="192" cy="118" r="5" fill="#273d30" /><circle cx="212" cy="118" r="5" fill="#273d30" />
          <path d="M200 99 H207 M200 104 H207" stroke="#386644" strokeWidth="2" />
        </motion.g>
        {!reduced && <motion.path key={"spark" + run} d="M235 78 L240 67 M246 79 L255 73 M251 90 L262 88"
          stroke="#a6f4bf" strokeWidth="2.5" strokeLinecap="round" fill="none"
          initial={{ opacity: 0 }} animate={{ opacity: [0, .9, 0] }}
          transition={{ delay: .9, duration: .65 }} />}
        <text x="116" y="189" textAnchor="middle" fill="#a6c4ac" fontSize="11">Neighbor A</text>
        <text x="398" y="189" textAnchor="middle" fill="#a6c4ac" fontSize="11">Neighbor B</text>
      </svg>
      <p role="status" className="pd-handoff-note">
        {delivered ? <><Check size={15} /> Handoff complete! Next person&apos;s turn.</>
          : <><ArrowLeftRight size={15} /> Shared-use illustration · no real delivery has occurred.</>}
      </p>
    </div>
  );
}

export function DemoTour({ displayName, onLive, onSignOut }: {
  displayName: string; onLive: () => void; onSignOut: () => void;
}) {
  const [stage, setStage] = useState<Stage>("needs");
  const [group, setGroup] = useState<GroupId>("washer");
  const [phase, setPhase] = useState<Phase>("awaiting_approval");
  const [selectedDay, setSelectedDay] = useState("2026-11-18");
  const [showExtract, setShowExtract] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState(false);
  const current = scenarios.find(s => s.id === group)!;
  const rows = useMemo(() => groupRows(group, phase), [group, phase]);
  const captured = rows.members.reduce((sum, m) => sum + m.captured_minor, 0) / 100;
  const progress = Math.round((captured / current.price) * 100);
  const timeline = [
    { id: "sample-1", slot: 1, start_date: "2026-11-16", end_date: "2026-11-17", is_you: true },
    { id: "sample-2", slot: 2, start_date: "2026-11-18", end_date: "2026-11-19", is_you: false },
    { id: "sample-3", slot: 3, start_date: "2026-11-20", end_date: "2026-11-21", is_you: false },
    { id: "sample-4", slot: 4, start_date: "2026-11-22", end_date: "2026-11-22", is_you: false },
  ];
  const selectedBooking = timeline.find(b => selectedDay >= b.start_date && selectedDay <= b.end_date);
  const heading = {
    needs: ["Understand the need.", "The first step is simply saying what you need."],
    quotes: ["Saved draft quotes", "Review the item, the example price and each proposed share before anyone is invited."],
    funding: ["Fund a shared possibility.", "Invite interested participants, collect explicit acceptance and approve each share separately."],
    ledger: ["Every contribution. Accounted for.", "Read-only records of member payment states and events—shown here as fictional AG Grid data."],
    schedule: ["One asset. Everyone's turn.", "A shared-use timeline shows who plans to use the item, and when."],
  }[stage];

  function go(next: Stage) { setStage(next); setShowGuide(false); }
  return (
    <div className="pd-root">
      <div className="pd-shell">
        <aside className="pd-sidebar">
          <div className="pd-brand"><span><Handshake size={20} /></span><div><strong>ONE <i>/</i> MANY</strong><small>Shared ownership, made clear.</small></div></div>
          <div className="pd-sidebar-label">PRODUCT FLOW</div>
          <nav className="pd-navigation" aria-label="Prototype navigation">
            {steps.map((step, i) => <button key={step.id} type="button" onClick={() => go(step.id)}
              className={stage === step.id ? "selected" : ""} aria-current={stage === step.id ? "step" : undefined}>
              <span className="pd-nav-num">{String(i + 1).padStart(2, "0")}</span>
              <span>{step.name}</span><ChevronRight size={15} />
            </button>)}
          </nav>
          <div className="pd-sidebar-bottom">
            <div className="pd-side-guide"><ShieldCheck size={19} /><strong>Prototype mode</strong><p>Every example is fictional. Sandbox captures and bookings are simulated here, never submitted to the API.</p></div>
            <button className="pd-live" onClick={onLive}>Open live workspace <ArrowUpRight size={16} /></button>
            <div className="pd-profile"><span>{displayName[0]?.toUpperCase() || "U"}</span><div><strong>{displayName}</strong><small>Exploring the prototype</small></div><button onClick={onSignOut} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button></div>
          </div>
        </aside>
        <main className="pd-main" id="main">
          <div className="pd-topline"><div><span className="pd-dot" /> INTERACTIVE PRODUCT PROTOTYPE</div><div><span className="pd-demo-label">DEMO · NOT REAL PAYMENTS</span><button onClick={onLive}>Live app <ArrowUpRight size={15} /></button></div></div>
          <div className="pd-heading">
            <span className="pd-kicker">{steps.find(step => step.id === stage)!.kicker}</span>
            <h1>{heading[0]}</h1>
            <p>{heading[1]}</p>
          </div>
          <div className="pd-context"><div><span className="pd-dot" /><strong>One consistent story, end to end</strong><small>Baner pressure washer · $400 · 4 prospective members</small></div>
            <button type="button" onClick={() => setShowGuide(v => !v)}><CircleHelp size={16} /> {showGuide ? "Hide guide" : "How to explore"}</button></div>
          {showGuide && <div className="pd-help" role="status">Start with the needs, follow a draft quote into funding, inspect simulated transaction states in the real AG Grid component, and see the handover in Bryntum Scheduler. Nothing here creates or modifies a PayPal order, database row, invitation, or actual booking.</div>}

          {stage === "needs" && <div className="pd-section">
            <div className="pd-section-row"><div><h2>Example requests</h2><p>Three fictional neighbors, with prewritten extraction results. Real AI extraction is in the live workspace.</p></div><button className="pd-quiet-button" onClick={onLive}><Sparkles size={16} /> Analyze a real need <ArrowUpRight size={15} /></button></div>
            <div className="pd-need-list">{needs.map((need, i) => <article className="pd-record" key={need.title}>
              <div className="pd-record-index">{String(i + 1).padStart(2, "0")}</div>
              <div className="pd-record-content"><div className="pd-record-head"><h3>{need.title}</h3><span className="pd-tag">{need.asset}</span></div><p>{need.description}</p><div className="pd-meta">{need.area} <span>·</span> {need.dates} <span>·</span> {need.matches} fictional matches</div>
                {showExtract === need.title && <div className="pd-extract"><Sparkles size={16} /><div><strong>Sample classification · not a Gemini response</strong><span>Item: {need.asset} · Purpose: {need.feature} · Reusable: Yes</span></div></div>}
              </div><div className="pd-record-actions">
                <button type="button" onClick={() => setShowExtract(showExtract === need.title ? null : need.title)}>Sample extraction</button>
                {need.group && <button className="pd-record-next" type="button" onClick={() => { setGroup(need.group!); go("quotes"); }}>View quote <ArrowRight size={15} /></button>}
              </div>
            </article>)}</div>
            <div className="pd-bottom-action"><button className="pd-primary" onClick={() => go("quotes")}>Next: draft quotes <ArrowRight size={16} /></button></div>
          </div>}

          {stage === "quotes" && <div className="pd-section">
            <div className="pd-section-row"><div><h2>Cost-sharing proposals</h2><p>Demo price snapshots, not live Channel3 merchant offers, commitments, or actual purchases.</p></div></div>
            <div className="pd-quote-list">{scenarios.map(s => <button key={s.id} type="button" className={"pd-quote" + (group === s.id ? " active" : "")} aria-pressed={group === s.id} onClick={() => setGroup(s.id)}>
              <div className="pd-quote-symbol"><FileText size={22} /></div><div className="pd-quote-text"><strong>{s.product}</strong><span>{s.description} · {s.area}</span><small>{s.ref} · Fictional offer, not verified by Channel3</small></div>
              <div className="pd-quote-amount"><small>Example price</small><strong>{money(s.price)}</strong><span>{money(s.price / s.people)} each for {s.people}</span></div><CheckCircle2 size={20} className="pd-quote-check" />
            </button>)}</div>
            <div className="pd-share-summary">
              <div><span>SELECTED DRAFT · {current.ref}</span><h3>{current.product}</h3><p>Equal illustrative shares, excluding tax, delivery and any actual agreement.</p></div>
              <div className="pd-share-split"><div><small>Item price</small><strong>{money(current.price)}</strong></div><span className="pd-divide">÷ {current.people}</span><div><small>Each proposed share</small><strong>{money(current.price / current.people)}</strong></div></div>
            </div>
            <div className="pd-bottom-action"><button className="pd-primary" onClick={() => go("funding")}>Next: group funding <ArrowRight size={16} /></button></div>
          </div>}

          {stage === "funding" && <div className="pd-section">
            <div className="pd-section-row"><div><h2>Accepted groups</h2><p>Pick a scenario to inspect member acceptance and payment states. This preview cannot contact PayPal.</p></div></div>
            <div className="pd-switcher" aria-label="Choose fictional funding group">{scenarios.map(s => <button key={s.id} type="button" className={group === s.id ? "active" : ""} aria-pressed={group === s.id} onClick={() => setGroup(s.id)}>{s.product}</button>)}</div>
            <div className="pd-funding-summary"><div><small>Fictional group · {current.product}</small><strong>{money(captured)} <span>/ {money(current.price)} simulated</span></strong><p>{rows.members.filter(r => r.payment_state === "completed").length} of {current.people} simulated captures completed · {progress}% of the example price</p></div><span className="pd-funding-state">{group === "washer" ? "Scenario complete" : "Scenario in progress"}</span></div>
            <div className="pd-progress" role="progressbar" aria-label="Fictional funding progress" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}><span style={{ width: progress + "%" }} /></div>
            <div className="pd-members">{rows.members.map(m => <div className="pd-member-row" key={m.slot}><span className="pd-member-avatar">{m.is_you ? "Y" : String(m.slot)}</span><div><strong>{m.is_you ? "You" : "Member " + m.slot}</strong><span>{m.payment_state.replaceAll("_", " ")}</span></div><b>{m.share_display}</b><span className={"pd-payment-tag " + (m.payment_state === "completed" ? "complete" : m.payment_state === "reversed" ? "reversed" : "")}>{m.payment_state === "completed" ? "Simulated captured" : m.payment_state.replaceAll("_", " ")}</span></div>)}</div>
            {group === "projector" && <div className="pd-simulation"><div><strong>Try the approval flow</strong><p>Only your fictional participant (Member 3) changes state. AG Grid will reflect it in the next step.</p></div>{phase === "awaiting_approval"
              ? <button className="pd-primary" onClick={() => setPhase("approved")}>Simulate approval <ArrowRight size={15} /></button>
              : phase === "approved" ? <button className="pd-primary" onClick={() => setPhase("completed")}>Simulate capture <ArrowRight size={15} /></button>
              : <button className="pd-quiet-button" onClick={() => setPhase("awaiting_approval")}><Check size={15} /> Reset simulation</button>}</div>}
            <p className="pd-warning"><ShieldCheck size={16} /> Fictitious member states, not verified PayPal events. Actual Sandbox authorization requires separate explicit approval in the live workspace.</p>
            <div className="pd-bottom-action"><button className="pd-primary" onClick={() => go("ledger")}>Next: inspect the ledger <ArrowRight size={16} /></button></div>
          </div>}

          {stage === "ledger" && <div className="pd-section">
            <div className="pd-section-row"><div><h2>Member contributions & event history</h2><p>Real AG Grid with fictional records. Sort, filter and export the sample CSV—no API payment records are involved.</p></div></div>
            <div className="pd-switcher" aria-label="Choose sample ledger">{scenarios.map(s => <button key={s.id} className={group === s.id ? "active" : ""} aria-pressed={group === s.id} type="button" onClick={() => setGroup(s.id)}>{s.product}</button>)}</div>
            <div className="pd-ledger-status"><div><small>Simulated captured</small><strong>{money(captured)}</strong></div><div><small>Target</small><strong>{money(current.price)}</strong></div><div><small>Outstanding in this scenario</small><strong>{money(current.price - captured)}</strong></div></div>
            <div className="pd-grid-wrap"><DemoLedgerGrid members={rows.members} events={rows.events} groupId={"fictional-" + group} demo /></div>
            <div className="pd-bottom-action"><button className="pd-primary" onClick={() => { setGroup("washer"); go("schedule"); }}>Next: shared scheduling <ArrowRight size={16} /></button></div>
          </div>}

          {stage === "schedule" && <div className="pd-section">
            <div className="pd-section-row"><div><h2>Pressure washer · shared calendar</h2><p>Fictional whole-day reservations for the fully-funded example scenario, rendered with Bryntum Scheduler Community.</p></div><span className="pd-tag">Nov 16–22, 2026</span></div>
            <div className="pd-timeline-shell"><DemoTimeline groupId="fictional-washer" reservations={timeline}
              ownWindow={{ start_date: "2026-11-16", end_date: "2026-11-17" }} /></div>
            <div className="pd-day-picker"><span>EXPLORE A DAY</span><div>{Array.from({ length: 7 }, (_, i) => { const value = "2026-11-" + String(i + 16); return <button key={value} type="button" onClick={() => setSelectedDay(value)} aria-pressed={selectedDay === value}>{i + 16}</button>; })}</div><strong>{selectedBooking ? selectedBooking.is_you ? "Your planned time" : "Member " + selectedBooking.slot + " · planned time" : "Unassigned in this sample"}</strong></div>
            <HandoffDrawing />
            <p className="pd-warning"><ShieldCheck size={16} /> The calendar and handover are fictional. Actual dates are saved only in the live app after verified Sandbox funding and conflict checks.</p>
            <div className="pd-bottom-action"><button className="pd-primary" onClick={onLive}>Try the real workspace <ArrowUpRight size={16} /></button></div>
          </div>}
          <div className="pd-footnote"><span>ONE / MANY · PRODUCT PROTOTYPE</span><span>Fictional data · no purchases, invitations or payments created</span></div>
        </main>
      </div>
    </div>
  );
}
