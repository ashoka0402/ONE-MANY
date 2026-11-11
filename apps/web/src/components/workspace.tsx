"use client";

import { FormEvent, useCallback, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowRight,
  CalendarDays,
  Check,
  CreditCard,
  Lightbulb,
  LoaderCircle,
  LogOut,
  Pencil,
  Plus,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

type Member = { id: string; email: string; display_name: string };
type AuthResponse = { access_token: string; expires_in: number; user: Member };
type Need = {
  id: string;
  request_text: string;
  location_label: string | null;
  needed_from: string | null;
  needed_until: string | null;
  status: "open" | "archived";
  created_at: string;
};
type NeedsPage = { items: Need[]; total: number };
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
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [needs, setNeeds] = useState<Need[]>([]);
  const [requestText, setRequestText] = useState("");
  const [locationLabel, setLocationLabel] = useState("");
  const [neededFrom, setNeededFrom] = useState("");
  const [neededUntil, setNeededUntil] = useState("");
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
        }),
      });
      setRequestText("");
      setLocationLabel("");
      setNeededFrom("");
      setNeededUntil("");
      setNotice("Need saved. AI matching will be added in Stage 2.");
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
      setNotice("Your need has been updated.");
      await refreshNeeds(token);
    } catch (err) {
      setError(messageFrom(err));
    } finally {
      setNeedBusy(false);
    }
  }

  function signOut() {
    setToken(null);
    setUser(null);
    setNeeds([]);
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
            <p>Tell us what you&apos;re looking for. Build a private list of needs today — collective purchasing comes next.</p>
            <div className="work-orbit" aria-hidden="true">
              <span className="work-orbit-center">1</span>
              <span className="work-orbit-dot a" /><span className="work-orbit-dot b" /><span className="work-orbit-dot c" />
            </div>
          </div>
          <span className="work-footnote">STAGE 1 · PRIVATE NEEDS, REAL ACCOUNTS</span>
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
            <p className="work-auth-disclaimer"><ShieldCheck size={15} /> No live purchases or payments are available yet.</p>
          </div>
        </section>
      </div>
    );
  }

  const openCount = needs.filter(need => need.status === "open").length;
  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        <Link href="/" className="wordmark">ONE <span>/</span> MANY</Link>
        <div className="workspace-label">YOUR SHARED SPACE</div>
        <nav aria-label="Workspace navigation">
          <a href="#needs" className="active"><Lightbulb size={18} /> Your needs</a>
          <a href="#next"><Users size={18} /> Shared groups</a>
          <a href="#next"><CreditCard size={18} /> Contributions</a>
          <a href="#next"><CalendarDays size={18} /> Scheduling</a>
        </nav>
        <div className="work-sidebar-profile"><div className="work-avatar">{user.display_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.display_name}</strong><span>{user.email}</span></div></div>
        <button className="work-logout" type="button" onClick={signOut}><LogOut size={16} /> Sign out</button>
      </aside>
      <div className="app-main">
        <header className="app-topbar"><span>Workspace / <strong>Your needs</strong></span><span className="outline-label">STAGE 1 · LIVE DATA</span></header>
        <main id="main" className="work-main">
          <section className="work-intro">
            <div><p className="eyebrow"><span className="status-dot" /> THE FIRST STEP</p><h1>What&apos;s on your<br /><em>mind today?</em></h1><p>Describe what you need. Your requests are private until matching is introduced.</p></div>
            <div className="work-count"><strong>{openCount}</strong><span>OPEN NEEDS</span></div>
          </section>
          {error && <p className="work-error" role="alert">{error}</p>}
          {notice && <p className="work-notice" role="status"><Check size={16} /> {notice}</p>}
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
                <button className="work-primary" type="submit" disabled={needBusy}>{needBusy ? <LoaderCircle size={17} className="work-spinner" /> : <Plus size={17} />} Save this need</button>
                <p className="work-helper"><ShieldCheck size={14} /> Only you can see or edit your needs during Stage 1.</p>
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
                      <div className="work-need-details">
                        {need.location_label && <span>{need.location_label}</span>}
                        {need.needed_from && <span>{need.needed_from}{need.needed_until ? ` to ${need.needed_until}` : ""}</span>}
                      </div>
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
          <section id="next" className="work-next">
            <div><span className="work-kicker">COMING IN THE NEXT STAGES</span><h2>Your needs become shared possibilities.</h2><p>AI demand matching, Channel3 products, PayPal contributions, and Bryntum scheduling are not connected yet.</p></div>
            <div className="work-next-icon" aria-hidden="true"><Users size={35} /></div>
          </section>
        </main>
      </div>
    </div>
  );
}
