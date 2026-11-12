"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity, ArrowDownLeft, ArrowRight, ArrowUpRight, Bell, CalendarDays,
  CheckCircle2, ChevronLeft, ChevronRight, CreditCard, Download, Handshake,
  LayoutDashboard, Lightbulb, LogOut, Menu, ReceiptText, Search,
  ShieldCheck, Sparkles, Users, Wallet, X,
} from "lucide-react";

type Screen = "overview" | "needs" | "groups" | "contributions" | "ledger" | "scheduling";
type Need = { title: string; kind: string; area: string; price: number; members: number; days: string; status: string; color: string; description: string };
type Group = { title: string; kind: string; price: number; joined: number; target: number; progress: number; status: string };
type Entry = { id: string; date: string; title: string; type: string; amount: number; status: string };

const NEEDS: Need[] = [
  { title: "Weekend pressure washer", kind: "Pressure washer", area: "Baner, Pune", price: 340, members: 3, days: "Nov 15–16", status: "Match ready", color: "mint", description: "A powerful washer to clean the driveway and patio." },
  { title: "Outdoor movie night", kind: "Portable projector", area: "Baner, Pune", price: 270, members: 3, days: "Nov 20–21", status: "Match ready", color: "blue", description: "A portable projector for movies with friends." },
  { title: "Apartment shelf project", kind: "Power drill", area: "Hinjawadi, Pune", price: 120, members: 2, days: "Nov 23–24", status: "Exploring", color: "gold", description: "A cordless drill for putting up shelves at home." },
  { title: "Neighborhood workshop", kind: "Camera", area: "Aundh, Pune", price: 480, members: 4, days: "Nov 27–28", status: "Draft", color: "purple", description: "A compact camera to record weekend lessons." },
];
const GROUPS: Group[] = [
  { title: "The clean-up crew", kind: "Pressure washer", price: 340, joined: 3, target: 3, progress: 67, status: "Funding preview" },
  { title: "Backyard cinema club", kind: "Portable projector", price: 270, joined: 2, target: 3, progress: 35, status: "Recruiting" },
  { title: "Build together", kind: "Power drill", price: 120, joined: 2, target: 2, progress: 100, status: "Scenario complete" },
];
const ENTRIES: Entry[] = [
  { id: "DEMO-1048", date: "Nov 12, 2026", title: "Washer · your share", type: "Contribution", amount: -113.34, status: "Sample captured" },
  { id: "DEMO-1047", date: "Nov 11, 2026", title: "Projector · planned share", type: "Planned", amount: -90, status: "Pending example" },
  { id: "DEMO-1046", date: "Nov 10, 2026", title: "Washer · member 2", type: "Contribution", amount: 113.33, status: "Sample captured" },
  { id: "DEMO-1045", date: "Nov 9, 2026", title: "Washer · member 3", type: "Contribution", amount: 113.33, status: "Sample captured" },
  { id: "DEMO-1044", date: "Nov 8, 2026", title: "Camera · draft estimate", type: "Planned", amount: -120, status: "Not charged" },
];
const TRENDS = [
  { label: "Shared needs", points: [27, 33, 31, 39, 43, 46, 42, 54, 58, 60, 65, 72, 79, 86] },
  { label: "Matches", points: [13, 19, 22, 29, 27, 35, 45, 39, 50, 52, 61, 68, 70, 76] },
  { label: "Est. savings", points: [15, 24, 28, 32, 30, 38, 42, 53, 49, 60, 67, 72, 78, 91] },
];
const NAV = [
  { key: "overview" as Screen, name: "Overview", icon: LayoutDashboard, badge: "" },
  { key: "needs" as Screen, name: "Your needs", icon: Lightbulb, badge: "4" },
  { key: "groups" as Screen, name: "Shared groups", icon: Users, badge: "3" },
  { key: "contributions" as Screen, name: "Contributions", icon: Wallet, badge: "2" },
  { key: "ledger" as Screen, name: "Contribution ledger", icon: ReceiptText, badge: "" },
  { key: "scheduling" as Screen, name: "Scheduling", icon: CalendarDays, badge: "3" },
];
const usd = (n: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);

function DemoBadge({ children = "FICTIONAL DEMO" }: { children?: ReactNode }) {
  return <span className="v-demo-badge"><span />{children}</span>;
}

function SectionHead({ kicker, title, subtitle, action }: { kicker: string; title: string; subtitle: string; action?: ReactNode }) {
  return <div className="v-section-head"><div><span className="v-kicker">{kicker}</span><h2>{title}</h2><p>{subtitle}</p></div>{action}</div>;
}

function ImpactChart({ selected }: { selected: number }) {
  const [hover, setHover] = useState<number | null>(null);
  const points = TRENDS[selected].points;
  const coords = points.map((n, i) => ({ x: 20 + i * (660 / (points.length - 1)), y: 178 - n * 1.5 }));
  const path = coords.map((p, i) => (i ? "L " : "M ") + p.x + " " + p.y).join(" ");
  const active = coords[hover ?? coords.length - 1];
  return <div className="v-chart">
    <svg viewBox="0 0 700 190" preserveAspectRatio="none" role="img" aria-label={"Fictional " + TRENDS[selected].label + " trend"}>
      <defs><linearGradient id="v-chart-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#72eab2" stopOpacity=".29" /><stop offset="1" stopColor="#72eab2" stopOpacity="0" /></linearGradient></defs>
      {[45, 92, 139].map(y => <line key={y} x1="0" x2="700" y1={y} y2={y} stroke="#ffffff" strokeOpacity=".06" strokeDasharray="4 7" />)}
      <path d={path + " L 680 190 L 20 190 Z"} fill="url(#v-chart-fill)" />
      <path d={path} stroke="#7aeabb" fill="none" strokeWidth="3" strokeLinejoin="round" />
      <line x1={active.x} x2={active.x} y1="0" y2="190" stroke="#fff" strokeOpacity=".2" strokeDasharray="4 7" />
      <circle cx={active.x} cy={active.y} r="6" stroke="#11291e" strokeWidth="3" fill="#9af8d0" />
      {coords.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r="14" fill="transparent" onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)} />)}
    </svg><div className="v-chart-legend"><span><i />{TRENDS[selected].label} · illustration</span><small>Not real historical data</small></div>
  </div>;
}

export function DemoTour({ displayName, onLive, onSignOut }: { displayName: string; onLive: () => void; onSignOut: () => void }) {
  const [screen, setScreen] = useState<Screen>("overview");
  const [search, setSearch] = useState("");
  const [trend, setTrend] = useState(0);
  const [card, setCard] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(0);
  const [matchOnly, setMatchOnly] = useState(false);
  const [day, setDay] = useState(2);
  const [calendarInfo, setCalendarInfo] = useState(false);
  const [help, setHelp] = useState(false);
  const [notification, setNotification] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const searchInput = useRef<HTMLInputElement>(null);
  const firstName = displayName.split(" ")[0] || "there";
  const matchingNeeds = useMemo(() => NEEDS.filter(n => (!matchOnly || n.status === "Match ready") && (n.title + n.kind + n.area).toLowerCase().includes(search.toLowerCase())), [search, matchOnly]);
  const matchingGroups = useMemo(() => GROUPS.filter(g => (g.title + g.kind).toLowerCase().includes(search.toLowerCase())), [search]);
  const matchingEntries = useMemo(() => ENTRIES.filter(e => (e.id + e.title + e.status + e.type).toLowerCase().includes(search.toLowerCase())), [search]);
  const bookings: Record<number, { asset: string; member: string; color: string }> = {
    1: { asset: "Pressure washer", member: "Member 1", color: "mint" },
    3: { asset: "Pressure washer", member: "Member 2", color: "blue" },
    5: { asset: "Portable projector", member: "You", color: "gold" },
  };

  useEffect(() => {
    function shortcuts(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault(); searchInput.current?.focus();
      }
      if (event.key === "Escape") { setHelp(false); setNotification(false); setMobileNav(false); }
    }
    window.addEventListener("keydown", shortcuts);
    return () => window.removeEventListener("keydown", shortcuts);
  }, []);

  function navigate(target: Screen) { setScreen(target); setSearch(""); setMobileNav(false); }
  function cycle(direction: number) { setCard(n => (n + NEEDS.length + direction) % NEEDS.length); setFlipped(false); }
  function exportCsv() {
    const rows = [["ID", "Date", "Title", "Type", "Amount USD", "Status", "Provenance"], ...ENTRIES.map(row => [row.id, row.date, row.title, row.type, String(row.amount), row.status, "FICTIONAL DEMO"])];
    const csv = rows.map(row => row.map(value => '"' + value.replaceAll('"', '""') + '"').join(",")).join("\n");
    const href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a"); a.href = href; a.download = "one-many-demo-ledger.csv";
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(href);
  }
  const item = NEEDS[card];

  return <div className="v-page"><div className="v-shell">
    <aside className={"v-sidebar" + (mobileNav ? " open" : "")}>
      <div className="v-brand"><span className="v-brand-mark"><Handshake size={23} /></span><div><strong>ONE <em>/</em> MANY</strong><small>Make more possible.</small></div><button className="v-close-nav" onClick={() => setMobileNav(false)} aria-label="Close menu"><X size={18} /></button></div>
      <div className="v-nav-caption">YOUR WORKSPACE</div><nav aria-label="Demo navigation" className="v-nav">{NAV.map(({ key, name, icon: Icon, badge }) =>
        <button key={key} onClick={() => navigate(key)} className={screen === key ? "active" : ""} aria-current={screen === key ? "page" : undefined}><Icon size={18} /><span>{name}</span>{badge && <i>{badge}</i>}</button>)}</nav>
      <div className="v-sidebar-rule" /><div className="v-nav-caption">DISCOVER</div><div className="v-nav"><button onClick={onLive}><Activity size={18} /><span>Real workspace</span><ArrowUpRight size={14} /></button><button onClick={() => setHelp(true)}><ShieldCheck size={18} /><span>Demo guide</span></button></div>
      <div className="v-sidebar-footer"><div className="v-savings-box"><small>Illustrative savings</small><strong>$466.00</strong><p>Across four example needs</p><div className="v-mini-progress"><span /></div></div><div className="v-person"><span>{firstName[0].toUpperCase()}</span><div><strong>{displayName}</strong><small>Demo preview</small></div><button onClick={onSignOut} aria-label="Sign out" title="Sign out"><LogOut size={17} /></button></div></div>
    </aside>
    {mobileNav && <button className="v-nav-scrim" onClick={() => setMobileNav(false)} aria-label="Close navigation" />}
    <div className="v-main">
      <header className="v-topbar"><button className="v-open-nav" onClick={() => setMobileNav(true)} aria-label="Open navigation"><Menu size={22} /></button><label className="v-search"><Search size={18} /><input ref={searchInput} value={search} onChange={e => setSearch(e.target.value)} placeholder="Search needs, groups, activity..." aria-label="Search demo records" /><kbd>⌘K</kbd></label><div className="v-top-actions"><DemoBadge /><button className="v-round-icon" onClick={() => setNotification(!notification)} aria-label="Notifications"><Bell size={19} /><i /></button><button className="v-user-circle" onClick={() => setHelp(true)} aria-label="About demo">{firstName[0].toUpperCase()}</button></div>{notification && <div className="v-notification"><strong>No real notifications</strong><p>This is a preview with fictional activity.</p><button onClick={() => setNotification(false)}>Close</button></div>}</header>
      <main className="v-content">
        {screen === "overview" && <>
          <div className="v-hero"><div><span className="v-kicker"><span className="v-pulse" /> YOUR WORLD, BETTER SHARED</span><h1>Good to see you, <em>{firstName}.</em></h1><p>Four shared possibilities, a few good neighbors, and a smarter way to own less.</p></div><div className="v-hero-buttons"><button className="v-outline" onClick={() => setHelp(true)}><ShieldCheck size={16} /> About this demo</button><button className="v-primary" onClick={onLive}><Sparkles size={17} /> Try real AI extraction <ArrowRight size={16} /></button></div></div>
          {search && <div className="v-panel v-search-result"><div className="v-panel-heading"><h3>Results for “{search}”</h3><button onClick={() => setSearch("")}>Clear <X size={14} /></button></div>{matchingNeeds.map(n => <button key={n.title} onClick={() => navigate("needs")}>{n.title}<ArrowRight size={14} /></button>)}{matchingGroups.map(g => <button key={g.title} onClick={() => navigate("groups")}>{g.title}<ArrowRight size={14} /></button>)}{!matchingNeeds.length && !matchingGroups.length && <p>No sample records matched.</p>}</div>}
          <div className="v-hero-grid">
            <section className="v-panel v-card-panel"><div className="v-panel-heading"><div><h3>Shared possibilities</h3><p>Tap the card to flip it and explore an example.</p></div><button onClick={() => navigate("needs")}>All needs <ArrowUpRight size={15} /></button></div>
              <div className="v-card-stage"><div className="v-stacked-card back" /><div className="v-stacked-card middle" /><button className={"v-asset-card " + item.color + (flipped ? " flipped" : "")} onClick={() => setFlipped(!flipped)} aria-label={flipped ? "Show card front" : "Flip card for details"}><div className="v-card-top"><span>ONE / MANY</span><span>◉</span></div>{flipped ? <div className="v-flip-content"><strong>{item.members} potential people</strong><span>Example equal share</span><b>{usd(item.price / item.members)}</b></div> : <><div className="v-card-icon"><Sparkles size={26} /></div><div className="v-card-bottom"><span><small>SHARED ASSET</small><strong>{item.kind}</strong></span><b>{"0" + (card + 1)}</b></div></>}</button></div>
              <div className="v-card-controls"><div><small>NOW EXPLORING</small><strong>{item.title}</strong><span>{item.area} · {item.days}</span></div><div><button onClick={() => cycle(-1)} aria-label="Previous need"><ChevronLeft size={18} /></button><button onClick={() => cycle(1)} aria-label="Next need"><ChevronRight size={18} /></button></div></div>
            </section>
            <section className="v-panel v-impact"><div className="v-panel-heading"><div><h3>Shared impact</h3><p>How this fictional community could grow</p></div><span className="v-green-tag"><ArrowUpRight size={14} /> Preview</span></div><div className="v-impact-numbers"><div><strong>$1,210<span>.00</span></strong><small>Combined illustrative product value</small></div><div><span><small>Needs</small><b>04</b></span><span><small>Matches</small><b>06</b></span><span><small>Groups</small><b>03</b></span></div></div><div className="v-chart-tabs">{TRENDS.map((t, i) => <button className={trend === i ? "active" : ""} onClick={() => setTrend(i)} key={t.label}>{t.label}</button>)}</div><ImpactChart selected={trend} /></section>
          </div>
          <div className="v-lower-grid"><section className="v-panel v-activity"><div className="v-panel-heading"><div><h3>Latest activity</h3><p>Sample transactions and milestones</p></div><button onClick={() => navigate("ledger")}>All activity <ArrowUpRight size={15} /></button></div>{ENTRIES.slice(0, 3).map(entry => <div className="v-activity-row" key={entry.id}><span className="v-activity-icon">{entry.amount > 0 ? <ArrowDownLeft size={19} /> : <CreditCard size={19} />}</span><div><strong>{entry.title}</strong><small>{entry.date} · {entry.status}</small></div><b>{usd(Math.abs(entry.amount))}</b></div>)}</section>
            <section className="v-panel v-upcoming"><div className="v-panel-heading"><div><h3>Coming up</h3><p>Illustrative shared-use calendar</p></div><button onClick={() => navigate("scheduling")}>Schedule <ArrowUpRight size={15} /></button></div>{[["16", "NOV", "Pressure washer", "Member 1 · Baner, Pune"],["21", "NOV", "Outdoor movie night", "You · Baner, Pune"]].map(row => <button className="v-upcoming-row" onClick={() => navigate("scheduling")} key={row[0]}><span><strong>{row[0]}</strong><small>{row[1]}</small></span><div><strong>{row[2]}</strong><small>{row[3]}</small></div><ChevronRight size={17} /></button>)}</section></div>
        </>}
        {screen === "needs" && <><SectionHead kicker="01 / YOUR NEEDS" title="The beginning of something shared." subtitle="Browse example needs and classifications. Only the live workspace runs Gemini."
          action={<button className="v-primary" onClick={onLive}><Sparkles size={17} /> Create & analyze a real need <ArrowRight size={15} /></button>} />
          <div className="v-ai-guide"><div className="v-ai-icon"><Sparkles size={23} /></div><div><strong>How AI extraction works</strong><p>Save a need in the live workspace, then click <b>Analyze with Gemini</b>. Gemini identifies the reusable asset, purpose and features. After opting into discovery, you can check for matches. The examples below are prewritten, not AI responses.</p></div><button onClick={onLive}>Try it live <ArrowUpRight size={15} /></button></div>
          <div className="v-list-toolbar"><div><strong>{matchingNeeds.length} sample needs</strong><small>Fictional examples · no real catalog prices</small></div><button className={matchOnly ? "active" : ""} onClick={() => setMatchOnly(!matchOnly)}>{matchOnly ? "✓ " : ""}Match ready only</button></div>
          <div className="v-needs-grid">{matchingNeeds.map((n, i) => <article className="v-panel v-need" key={n.title}><div className="v-need-top"><span className={"v-kind-icon " + n.color}><Lightbulb size={22} /></span><span className="v-status">{n.status}</span></div><h3>{n.title}</h3><p>{n.description}</p><div className="v-need-meta"><span>{n.area}</span><span>{n.days}</span></div><div className="v-need-ai"><small><Sparkles size={13} /> PREWRITTEN CLASSIFICATION</small><strong>{n.kind}</strong><span>Reusable asset · example only</span></div><div className="v-need-bottom"><div><small>Potential members</small><strong>{n.members}</strong></div><div><small>Example share</small><strong>{usd(n.price / n.members)}</strong></div><button aria-label={"View group for " + n.title} onClick={() => { setExpanded(i); navigate("groups"); }}><ArrowUpRight size={18} /></button></div></article>)}</div>
          {!matchingNeeds.length && <div className="v-panel v-empty">No sample needs match that search.</div>}
        </>}
        {screen === "groups" && <><SectionHead kicker="02 / SHARED GROUPS" title="Better, together." subtitle="Fictional neighborhood groups demonstrate membership and funding stages without creating actual PayPal orders." action={<button className="v-outline" onClick={onLive}>Manage real groups <ArrowUpRight size={16} /></button>} />
          <div className="v-stat-strip"><div><small>Sample groups</small><strong>03</strong></div><div><small>Fictional member slots</small><strong>07</strong></div><div><small>Illustrative value</small><strong>$730</strong></div></div>
          <div className="v-groups-grid">{matchingGroups.map(g => { const i = GROUPS.indexOf(g);return <article key={g.title} className="v-panel v-group"><div className="v-group-top"><span className="v-group-icon"><Handshake size={23} /></span><span className="v-status">{g.status}</span></div><small className="v-kicker">{g.kind.toUpperCase()}</small><h3>{g.title}</h3><p>{g.joined} / {g.target} fictional participants</p><strong className="v-group-amount">{usd(g.price)}</strong><span className="v-muted">Hypothetical item price</span><div className="v-progress-label"><span>Scenario progress</span><b>{g.progress}%</b></div><div className="v-progress"><span style={{ width: g.progress + "%" }} /></div><button className="v-group-expand" onClick={() => setExpanded(expanded === i ? null : i)} aria-expanded={expanded === i}>Group details <ChevronRight size={17} /></button>{expanded === i && <div className="v-group-details"><div><span>Example equal share</span><strong>{usd(g.price / g.target)}</strong></div><div><span>Possible members</span><strong>{g.joined} of {g.target}</strong></div><p>Sample only: no real people were invited or charged.</p><button onClick={() => navigate("contributions")}>Preview contributions <ArrowRight size={15} /></button></div>}</article>; })}</div>
          {!matchingGroups.length && <div className="v-panel v-empty">No matching sample groups.</div>}
        </>}
        {screen === "contributions" && <><SectionHead kicker="03 / CONTRIBUTIONS" title="A little from everyone." subtitle="Explore a group payment scenario. Fictional amounts below are not verified Sandbox captures." action={<button className="v-outline" onClick={() => navigate("ledger")}>View sample ledger <ArrowUpRight size={16} /></button>} />
          <div className="v-contrib-grid"><div className="v-panel v-contrib-hero"><span className="v-kicker">ILLUSTRATIVE GROUP PROGRESS</span><h3>$226.67 <span>/ $340.00</span></h3><p>Example: The clean-up crew</p><div className="v-progress large"><span style={{ width: "66.7%" }} /></div><div className="v-progress-label"><span>0%</span><span>67% scenario complete</span><span>100%</span></div><div className="v-contrib-notice"><ShieldCheck size={19} /><span>In live mode, contributions count only after individual PayPal Sandbox approval and verification.</span></div></div>
            <div className="v-panel v-members"><h3>Member shares</h3>{[["You", "$113.34", "Sample captured"],["Member 2", "$113.33", "Sample captured"],["Member 3", "$113.33", "Pending example"]].map((m, i) => <div className="v-member" key={m[0]}><span className={"v-member-avatar m" + i}>{m[0][0]}</span><div><strong>{m[0]}</strong><small>{m[2]}</small></div><b>{m[1]}</b></div>)}<small className="v-muted">Every member and status on this page is invented.</small></div></div>
          <section className="v-panel v-flow"><div className="v-panel-heading"><div><h3>From possibility to participation</h3><p>Live funding flow · every member must explicitly opt in</p></div></div><div className="v-flow-steps">{[["01", "Invite", "Share a group code"],["02", "Accept", "Choose a matching need"],["03", "Approve", "PayPal Sandbox"],["04", "Verify", "Reconcile the capture"]].map(step => <div key={step[0]}><span>{step[0]}</span><strong>{step[1]}</strong><small>{step[2]}</small></div>)}</div><button className="v-primary" onClick={onLive}>Open live funding <ArrowRight size={15} /></button></section>
        </>}
        {screen === "ledger" && <><SectionHead kicker="04 / CONTRIBUTION LEDGER" title="Every detail, accounted for." subtitle="Searchable and downloadable fictional ledger entries. No sample row is a real payment or audit event." action={<button className="v-outline" onClick={exportCsv}><Download size={17} /> Export demo CSV</button>} />
          <div className="v-ledger-stats"><div className="v-panel"><small>Example product value</small><strong>$730.00</strong><span>Illustration only</span></div><div className="v-panel"><small>Example shared amount</small><strong>$226.67</strong><span>Not a PayPal capture</span></div><div className="v-panel"><small>Sample entries</small><strong>05</strong><span>Fictional records</span></div></div><div className="v-panel v-ledger-box"><div className="v-panel-heading"><div><h3>Activity details</h3><p>Use the top search bar to filter the ledger</p></div><DemoBadge>SIMULATED LEDGER</DemoBadge></div><div className="v-table-scroll"><table className="v-table"><thead><tr><th>ENTRY</th><th>DETAILS</th><th>CATEGORY</th><th>AMOUNT</th><th>STATUS</th></tr></thead><tbody>{matchingEntries.map(row => <tr key={row.id}><td><span>{row.id}</span><small>{row.date}</small></td><td><strong>{row.title}</strong></td><td>{row.type}</td><td className={row.amount > 0 ? "v-income" : ""}>{row.amount < 0 ? "−" : "+"}{usd(Math.abs(row.amount))}</td><td><span className="v-status">{row.status}</span></td></tr>)}</tbody></table>{!matchingEntries.length && <div className="v-empty">No sample rows found.</div>}</div><p className="v-ledger-note"><ShieldCheck size={16} /> Live records are read-only and reconciled against verified Sandbox captures.</p></div>
        </>}
        {screen === "scheduling" && <><SectionHead kicker="05 / SCHEDULING" title="Your time. Shared on your terms." subtitle="Try the fictional shared-use calendar. Changes here do not alter persisted reservations." action={<button className="v-outline" onClick={onLive}>Open real scheduler <ArrowUpRight size={16} /></button>} />
          <div className="v-schedule-grid"><section className="v-panel v-calendar"><div className="v-panel-heading"><div><h3>November 16–22, 2026</h3><p>Example shared-use calendar · whole-day reservations</p></div><span className="v-status">3 sample bookings</span></div><div className="v-calendar-days">{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d, i) => <button key={d} className={day === i ? "active" : ""} onClick={() => { setDay(i); setCalendarInfo(false); }} aria-pressed={day === i}><small>{d}</small><strong>{i + 16}</strong>{bookings[i] && <i />}</button>)}</div><span className="v-kicker">SELECTED DAY · {["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][day]} {day + 16}</span>{bookings[day] ? <button className={"v-booking " + bookings[day].color} onClick={() => setCalendarInfo(!calendarInfo)}><span className="v-booking-dot" /><div><strong>{bookings[day].asset}</strong><small>{bookings[day].member} · Fictional all-day use</small></div><ChevronRight size={18} /></button> : <div className="v-calendar-empty"><CalendarDays size={24} /> Available in this example</div>}{calendarInfo && <p className="v-booking-info">This is an example booking only. The real app checks overlaps and permissions before saving a reservation.</p>}</section><section className="v-panel v-schedule-info"><span className="v-kicker">SHARE SMARTER</span><h3>One asset.<br /><em>Everyone gets a turn.</em></h3><p>Flexible shared-use schedules, without the confusion. Switch to the live scheduler to create a real, conflict-checked booking.</p>{["Member-owned date windows", "PostgreSQL conflict protection", "Verified Sandbox funding required"].map(v => <div className="v-checkline" key={v}><CheckCircle2 size={18} />{v}</div>)}<button className="v-primary" onClick={onLive}>Try real scheduling <ArrowRight size={15} /></button></section></div>
        </>}
        <footer className="v-footer"><ShieldCheck size={15} /><span>Fictional interactive preview. Use the <b>real workspace</b> for Gemini extraction, genuine opt-in groups and verified Sandbox activity.</span><button onClick={onLive}>Live workspace <ArrowUpRight size={14} /></button></footer>
      </main>
    </div>
  </div>
  {help && <div className="v-modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) setHelp(false); }}><section className="v-modal" role="dialog" aria-modal="true" aria-labelledby="v-modal-title"><button className="v-modal-close" onClick={() => setHelp(false)} aria-label="Close"><X size={19} /></button><div className="v-ai-icon"><Sparkles size={23} /></div><DemoBadge /><h2 id="v-modal-title">Explore without risk.</h2><p>The five sections contain fictional preview data. No real users, payments, inventory or reservations are created by these interactions.</p><div className="v-modal-guide"><strong>To use actual Gemini extraction:</strong><span>1. Put <code>GEMINI_API_KEY</code> in <code>apps/api/.env</code>.</span><span>2. Restart FastAPI and switch to the real workspace.</span><span>3. Save a need, then click <b>Analyze with Gemini</b>.</span></div><button className="v-primary" onClick={() => { setHelp(false); onLive(); }}>Open real workspace <ArrowRight size={15} /></button></section></div>}
  </div>;
}
