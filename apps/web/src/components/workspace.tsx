"use client";

import { FormEvent, useCallback, useState } from "react";
import Link from "next/link";
import { CatalogPanel, ProposalHistory } from "@/components/catalog-panel";
import { FundingPanel } from "@/components/funding-panel";
import { ReservationPanel } from "@/components/reservation-panel";
import { LedgerPanel } from "@/components/ledger-panel";
import { DemoTour } from "@/components/demo-tour";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  Lightbulb,
  LoaderCircle,
  LogOut,
  Pencil,
  Plus,
  ShieldCheck,
  Sparkles,
  Search,
} from "lucide-react";

type Member = { id: string; email: string; display_name: string };
type AuthResponse = { access_token: string; expires_in: number; user: Member };
type Intent = {
  asset_type: string;
  purpose: string;
  required_features: string[];
  excluded_features: string[];
  shareable: boolean;
  model_name: string;
};
type MatchSummary = {
  need_id: string;
  asset_type: string;
  potential_members: number;
  non_overlapping_schedules: number;
  scheduling_confirmation_required: number;
  candidates_limited: boolean;
  explanation: string;
};
type Need = {
  id: string;
  request_text: string;
  location_label: string | null;
  needed_from: string | null;
  needed_until: string | null;
  status: "open" | "archived";
  discoverable: boolean;
  intent: Intent | null;
  created_at: string;
};
type NeedsPage = { items: Need[]; total: number };
type WorkspaceStage = "needs" | "quotes" | "funding" | "ledger" | "schedule";
const liveStages: { id: WorkspaceStage; label: string }[] = [
  { id: "needs", label: "Needs & AI" },
  { id: "quotes", label: "Draft quotes" },
  { id: "funding", label: "Group funding" },
  { id: "ledger", label: "Contribution ledger" },
  { id: "schedule", label: "Shared scheduling" },
];
type ApiError = { error?: { message?: string } };

const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

async function api<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}/api/v1${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });
  if (response.status === 204) return undefined as T;
  const data = (await response.json().catch(() => null)) as (T & ApiError) | null;
  if (!response.ok) {
    throw new Error(data?.error?.message || `Request failed (${response.status})`);
  }
  return data as T;
}

function messageFrom(error: unknown): string {
  if (error instanceof TypeError) return "Cannot reach the API. Start FastAPI and check NEXT_PUBLIC_API_URL.";
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

export function Workspace() {
  // Access tokens stay in memory only: refresh or closing the tab requires login again.
  // Stage 1 intentionally avoids long-lived JavaScript-accessible token storage.
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<Member | null>(null);
  const [mode, setMode] = useState<"register" | "login">("register");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authBusy, setAuthBusy] = useState(false);
  const [needBusy, setNeedBusy] = useState(false);
  const [loadingNeeds, setLoadingNeeds] = useState(false);
  const [demoBusy, setDemoBusy] = useState(false);
  const [demoView, setDemoView] = useState(process.env.NODE_ENV !== "production");
  const [activeSection, setActiveSection] = useState<WorkspaceStage>("needs");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [needs, setNeeds] = useState<Need[]>([]);
  const [requestText, setRequestText] = useState("");
  const [locationLabel, setLocationLabel] = useState("");
  const [neededFrom, setNeededFrom] = useState("");
  const [neededUntil, setNeededUntil] = useState("");
  const [discoveryOptIn, setDiscoveryOptIn] = useState(false);
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [matchingId, setMatchingId] = useState<string | null>(null);
  const [matchResults, setMatchResults] = useState<Record<string, MatchSummary>>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState("");

  const refreshNeeds = useCallback(async (accessToken: string) => {
    setLoadingNeeds(true);
    try {
      const page = await api<NeedsPage>("/needs?limit=100", accessToken);
      setNeeds(page.items);
      setError("");
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setLoadingNeeds(false);
    }
  }, []);

  async function loadDemoExamples() {
    if (!token) return;
    setDemoBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await api<{
        created_needs: number;
        created_sample_neighbors: number;
        message: string;
      }>("/demo/seed", token, { method: "POST" });
      await refreshNeeds(token);
      setNotice(result.created_needs > 0
        ? `Loaded ${result.created_needs} fictional needs and matching examples. No payments were created.`
        : "Demo examples are already loaded. No duplicates created.");
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setDemoBusy(false);
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthBusy(true);
    setError("");
    try {
      const payload = mode === "register"
        ? { email, password, display_name: name }
        : { email, password };
      const response = await api<AuthResponse>(
        mode === "register" ? "/auth/register" : "/auth/login",
        null,
        { method: "POST", body: JSON.stringify(payload) },
      );
      setUser(response.user);
      setToken(response.access_token);
      void refreshNeeds(response.access_token);
      setPassword("");
      setNotice("Your private workspace is ready.");
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    if (neededFrom && neededUntil && neededUntil < neededFrom) {
      setError("The end date must be on or after the start date.");
      return;
    }
    setNeedBusy(true);
    setError("");
    setNotice("");
    try {
      await api<Need>("/needs", token, {
        method: "POST",
        body: JSON.stringify({
          request_text: requestText,
          location_label: locationLabel || null,
          needed_from: neededFrom || null,
          needed_until: neededUntil || null,
          discoverable: discoveryOptIn,
        }),
      });
      setRequestText("");
      setLocationLabel("");
      setNeededFrom("");
      setNeededUntil("");
      setDiscoveryOptIn(false);
      setNotice("Need saved. Analyze it with Gemini when ready.");
      await refreshNeeds(token);
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setNeedBusy(false);
    }
  }

  async function updateNeed(id: string, changes: Record<string, unknown>) {
    if (!token) return;
    setNeedBusy(true);
    setError("");
    setNotice("");
    try {
      await api<Need>(`/needs/${id}`, token, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      setEditingId(null);
      setMatchResults(current => { const next = { ...current }; delete next[id]; return next; });
      setNotice("Your need has been updated.");
      await refreshNeeds(token);
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setNeedBusy(false);
    }
  }

  async function analyzeNeed(id: string) {
    if (!token) return;
    setAnalyzingId(id);
    setError("");
    setNotice("");
    try {
      const intent = await api<Intent>(`/needs/${id}/analyze`, token, { method: "POST" });
      setMatchResults(current => { const next = { ...current }; delete next[id]; return next; });
      setNotice(intent.shareable
        ? `Gemini identified a reusable asset: ${intent.asset_type}. You can now check compatible needs.`
        : "Gemini classified this request as unsuitable for shared physical ownership.");
      await refreshNeeds(token);
    } catch (err) {
      setError(messageFrom(err) + " Verify GEMINI_API_KEY is configured on the API server.");
    } finally {
      setAnalyzingId(null);
    }
  }

  async function findMatchesFor(id: string) {
    if (!token) return;
    setMatchingId(id);
    setError("");
    setNotice("");
    try {
      const result = await api<MatchSummary>(`/needs/${id}/matches`, token);
      setMatchResults(current => ({ ...current, [id]: result }));
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setMatchingId(null);
    }
  }

  function signOut() {
    setToken(null);
    setUser(null);
    setNeeds([]);
    setMatchResults({});
    setEditingId(null);
    setError("");
    setNotice("");
  }

  if (!token || !user) {
    return (
      <div className="work-auth-layout">
        <section className="work-auth-story">
          <Link href="/" className="wordmark">ONE <span>/</span> MANY</Link>
          <div className="work-auth-copy">
            <span className="work-kicker"><Sparkles size={14} /> THE START OF SOMETHING SHARED</span>
            <h1>Have a need?<br /><em>Find your people.</em></h1>
            <p>Tell us what you&apos;re looking for. Discover compatible needs, consider real products, and join funding only with your explicit consent.</p>
            <div className="work-orbit" aria-hidden="true">
              <span className="work-orbit-center">1</span>
              <span className="work-orbit-dot a" /><span className="work-orbit-dot b" /><span className="work-orbit-dot c" />
            </div>
          </div>
          <span className="work-footnote">PAYPAL SANDBOX · DEMONSTRATION</span>
        </section>
        <section className="work-auth-panel">
          <div className="work-auth-card">
            <Link href="/" className="work-back"><ArrowLeft size={15} /> Back to the idea</Link>
            <div className="work-auth-heading">
              <span className="work-kicker">YOUR SHARED SPACE</span>
              <h2>{mode === "register" ? "Let's get started." : "Welcome back."}</h2>
              <p>{mode === "register" ? "Create your account to save your needs privately." : "Sign in to return to your saved needs."}</p>
            </div>
            <form onSubmit={handleAuth} className="work-form">
              {mode === "register" && (
                <label>Display name
                  <input value={name} onChange={event => setName(event.target.value)} required minLength={2} maxLength={80} autoComplete="name" placeholder="Your name" />
                </label>
              )}
              <label>Email address
                <input value={email} onChange={event => setEmail(event.target.value)} required type="email" maxLength={254} autoComplete="email" placeholder="you@example.com" />
              </label>
              <label>Password
                <input value={password} onChange={event => setPassword(event.target.value)} type="password" required minLength={mode === "register" ? 12 : undefined} autoComplete={mode === "register" ? "new-password" : "current-password"} placeholder={mode === "register" ? "At least 12 characters" : "Your password"} />
              </label>
              {error && <p className="work-error" role="alert">{error}</p>}
              <button type="submit" className="work-primary" disabled={authBusy}>
                {authBusy ? <LoaderCircle className="work-spinner" size={18} /> : mode === "register" ? "Create account" : "Sign in"}
                {!authBusy && <ArrowRight size={18} />}
              </button>
            </form>
            <p className="work-auth-switch">
              {mode === "register" ? "Already have an account?" : "New to ONE / MANY?"}{" "}
              <button type="button" onClick={() => { setMode(mode === "register" ? "login" : "register"); setError(""); }}>
                {mode === "register" ? "Sign in" : "Create account"}
              </button>
            </p>
            <p className="work-auth-disclaimer"><ShieldCheck size={15} /> Any payments are PayPal Sandbox simulations. No real money or purchases.</p>
          </div>
        </section>
      </div>
    );
  }

  if (demoView) {
    return (
      <DemoTour
        displayName={user.display_name}
        onLive={() => setDemoView(false)}
        onSignOut={signOut}
      />
    );
  }

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <Link href="/" className="wordmark">ONE <span>/</span> MANY</Link>
        <div className="workspace-label">YOUR WORKFLOW</div>
        <nav aria-label="Workspace navigation" className="work-step-navigation">
          {liveStages.map((step, index) => (
            <button key={step.id} type="button" onClick={() => setActiveSection(step.id)}
              className={activeSection === step.id ? "is-active" : ""}
              aria-current={activeSection === step.id ? "step" : undefined}>
              <span className="work-nav-number">{String(index + 1).padStart(2, "0")}</span>
              <span>{step.label}</span><ArrowRight size={14} />
            </button>
          ))}
        </nav>
        <button className="work-tour-link" type="button" onClick={() => setDemoView(true)}><Sparkles size={16} /> Explore complete prototype <ArrowRight size={14} /></button>
        <div className="work-sidebar-profile"><div className="work-avatar">{user.display_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.display_name}</strong><span>{user.email}</span></div></div>
        <button className="work-logout" type="button" onClick={signOut}><LogOut size={16} /> Sign out</button>
      </aside>
      <div className="app-main">
        <header className="app-topbar"><span>ONE / MANY / <strong>{liveStages.find(step => step.id === activeSection)?.label}</strong></span><button type="button" className="work-tour-topbutton" onClick={() => setDemoView(true)}><Sparkles size={15} /> View fictional walkthrough <ArrowRight size={14} /></button></header>
        <main id="main" className="work-main">
          {activeSection === "needs" && <>
          <section className="work-intro">
            <div><p className="eyebrow"><span className="status-dot" /> 01 / DISCOVERY</p><h1>What&apos;s on your<br /><em>mind today?</em></h1><p>Describe the thing you need. Analyze it with Gemini, then choose whether to find compatible people.</p></div>
          </section>
          <section className="work-demo-banner" aria-label="Product prototype">
            <div><strong>Want to see the complete product in action?</strong>
              <p>Explore populated quotes, group approvals, AG Grid records and the Bryntum timeline. All fictional and separate from your account.</p></div>
            <button type="button" onClick={() => setDemoView(true)}><Sparkles size={15} /> Explore five-stage prototype</button>
          </section>
          {process.env.NODE_ENV !== "production" && (
            <div className="work-seed-note">
              <span>Need realistic sample requests in your local database?</span>
              <button type="button" onClick={() => void loadDemoExamples()} disabled={demoBusy || loadingNeeds}>
                {demoBusy ? <LoaderCircle size={14} className="work-spinner" /> : <Lightbulb size={14} />}
                {demoBusy ? "Adding sample needs…" : "Add four sample needs only"}
              </button>
            </div>
          )}
          {error && <p className="work-error" role="alert">{error}</p>}
          {notice && <p className="work-notice" role="status"><Check size={16} /> {notice}</p>}
          <div className="work-ai-instruction"><span><Sparkles size={18} /></span><div><strong>Real Gemini extraction</strong><p>Save a need, then click <b>Analyze with Gemini</b>. Requires <code>GEMINI_API_KEY</code> in your API environment. Nothing is sent to Gemini until you explicitly click Analyze.</p></div></div>
          <div className="work-content">
            <section id="needs" className="work-create-card" aria-labelledby="create-title">
              <div className="work-card-title"><span className="work-kicker">01 / TELL US</span><h2 id="create-title">Add a new need</h2></div>
              <form className="work-form" onSubmit={handleCreate}>
                <label>What do you need?
                  <textarea required minLength={12} maxLength={2000} value={requestText} onChange={event => setRequestText(event.target.value)} rows={5} placeholder="I need a pressure washer to clean my patio this weekend..." />
                </label>
                <label>Neighborhood or general location (optional)
                  <input maxLength={120} value={locationLabel} onChange={event => setLocationLabel(event.target.value)} placeholder="e.g. Baner, Pune" />
                </label>
                <div className="work-date-row">
                  <label>From (optional)<input type="date" value={neededFrom} onChange={event => setNeededFrom(event.target.value)} /></label>
                  <label>Until (optional)<input type="date" value={neededUntil} onChange={event => setNeededUntil(event.target.value)} min={neededFrom || undefined} /></label>
                </div>
                <label className="work-consent">
                  <input type="checkbox" checked={discoveryOptIn} onChange={event => setDiscoveryOptIn(event.target.checked)} />
                  <span><strong>Join anonymous community discovery</strong><small>Allow eligible users in the same self-reported area to see anonymous match counts, not your message or identity. You may turn this off later.</small></span>
                </label>
                <button className="work-primary" type="submit" disabled={needBusy}>{needBusy ? <LoaderCircle size={17} className="work-spinner" /> : <Plus size={17} />} Save this need</button>
                <p className="work-helper"><ShieldCheck size={14} /> Your full request stays private. AI analysis is only sent to Gemini when you select Analyze.</p>
              </form>
            </section>
            <section className="work-list-card" aria-labelledby="list-title">
              <div className="work-card-title"><span className="work-kicker">02 / KEEP TRACK</span><h2 id="list-title">Saved needs</h2></div>
              {loadingNeeds ? <p className="work-empty"><LoaderCircle className="work-spinner" size={22} /> Loading your needs...</p> :
                needs.length === 0 ? <div className="work-empty"><Lightbulb size={34} strokeWidth={1.4} /><h3>Nothing here yet.</h3><p>Your first need is the beginning of something shared.</p></div> :
                <div className="work-list">
                  {needs.map(need => (
                    <article className={`work-need ${need.status === "archived" ? "is-archived" : ""}`} key={need.id}>
                      <div className="work-need-head"><span className={`work-status ${need.status}`}>{need.status}</span><span>{new Date(need.created_at).toLocaleDateString()}</span></div>
                      {editingId === need.id ? (
                        <form onSubmit={event => { event.preventDefault(); void updateNeed(need.id, { request_text: editingText }); }} className="work-edit-form">
                          <label htmlFor={`edit-${need.id}`}>Edit description</label>
                          <textarea id={`edit-${need.id}`} value={editingText} onChange={event => setEditingText(event.target.value)} minLength={12} maxLength={2000} required rows={3} />
                          <div><button type="submit" disabled={needBusy}>Save</button><button type="button" onClick={() => setEditingId(null)}>Cancel</button></div>
                        </form>
                      ) : <p className="work-need-text">{need.request_text}</p>}
                      <div className="work-need-analysis">
                        {need.intent ? (
                          <div className="work-intent-card">
                            <div className="work-intent-label"><Sparkles size={13} /> {need.intent.model_name === "demo-fixture"
                              ? "SAMPLE CLASSIFICATION · NOT AI-GENERATED"
                              : `GEMINI EXTRACTED · ${need.intent.model_name}`}</div>
                            <strong>{need.intent.asset_type}</strong>
                            <p>{need.intent.purpose}</p>
                            {need.intent.required_features.length > 0 && <small>Required: {need.intent.required_features.join(", ")}</small>}
                            {need.intent.excluded_features.length > 0 && <small>Excluded: {need.intent.excluded_features.join(", ")}</small>}
                            <small>{need.intent.shareable ? "Potentially reusable · awaiting real product validation" : "Not a suitable shared physical asset"}</small>
                          </div>
                        ) : <p className="work-unprocessed">AI extraction not run for this need yet.</p>}
                      </div>
                      <div className="work-need-details">
                        {need.location_label && <span>{need.location_label}</span>}
                        {need.needed_from && <span>{need.needed_from}{need.needed_until ? ` to ${need.needed_until}` : ""}</span>}
                      </div>
                      {need.status === "open" && (
                        <div className="work-match-actions">
                          <label className="work-discovery-toggle">
                            <input
                              type="checkbox"
                              checked={need.discoverable}
                              disabled={needBusy}
                              onChange={event => void updateNeed(need.id, { discoverable: event.target.checked })}
                            />
                            <span>{need.discoverable ? "Discoverable to anonymous matching" : "Private — enable matching"}</span>
                          </label>
                          <div className="work-action-buttons">
                            <button type="button" disabled={analyzingId !== null || needBusy} onClick={() => void analyzeNeed(need.id)}>
                              {analyzingId === need.id ? <LoaderCircle size={14} className="work-spinner" /> : <Sparkles size={14} />}
                              {need.intent ? "Recheck AI extraction" : "Analyze with Gemini"}
                            </button>
                            <button type="button" disabled={!need.intent?.shareable || !need.discoverable || !need.location_label || matchingId !== null} onClick={() => void findMatchesFor(need.id)}>
                              {matchingId === need.id ? <LoaderCircle size={14} className="work-spinner" /> : <Search size={14} />}
                              Find potential matches
                            </button>
                          </div>
                        </div>
                      )}
                      {matchResults[need.id] && (
                        <div className="work-match-result" role="status">
                          <strong>{matchResults[need.id].potential_members} potential {matchResults[need.id].potential_members === 1 ? "member" : "members"}</strong>
                          <span>{matchResults[need.id].non_overlapping_schedules} have distinct date windows; {matchResults[need.id].scheduling_confirmation_required} need scheduling confirmation.</span>
                          <p>{matchResults[need.id].explanation}</p>
                          {matchResults[need.id].candidates_limited && <small>Search limit reached; there may be additional opportunities.</small>}
                        </div>
                      )}
                      {need.status === "open" && need.intent?.shareable && need.discoverable && (
                        <CatalogPanel
                          key={need.id + need.request_text}
                          needId={need.id}
                          token={token}
                          potentialMembers={matchResults[need.id]?.potential_members ?? null}
                        />
                      )}
                      <div className="work-need-actions">
                        <button disabled={needBusy} onClick={() => { setEditingId(need.id); setEditingText(need.request_text); }}><Pencil size={14} /> Edit</button>
                        <button disabled={needBusy} onClick={() => void updateNeed(need.id, { status: need.status === "open" ? "archived" : "open" })}>{need.status === "open" ? "Archive" : "Reopen"}</button>
                      </div>
                    </article>
                  ))}
                </div>}
              {needs.length >= 100 && <p className="work-helper">Displaying the latest 100 needs; API pagination is available.</p>}
            </section>
          </div>
          </>}
          {activeSection === "quotes" && <div id="quotes" className="work-stage-section"><ProposalHistory token={token} /></div>}
          {activeSection === "funding" && <div className="work-stage-section"><FundingPanel token={token} needs={needs} /></div>}
          {activeSection === "ledger" && <div className="work-stage-section"><LedgerPanel token={token} /></div>}
          {activeSection === "schedule" && <div className="work-stage-section"><ReservationPanel token={token} /></div>}
        </main>
      </div>
    </div>
  );
}
